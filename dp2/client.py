import requests
import re

from urlparse import urlsplit, urljoin

from bs4 import BeautifulSoup
from dp2 import PROPERTY_TYPES, H_AJAX, H_COMMON, H_FORM
from dp2.resource import County, RegionStats, Property


class DaftClient(object):
    def __init__(self, redis):
        self.redis = redis
        self.session = requests.Session()
        self.logged_in = False

    def login(self, user, passwd):
        url = "http://www.daft.ie/my-daft/"
        resp = self.session.post(
                url,
                headers=H_FORM,
                data={
                    "auth[username]": user,
                    "auth[password]": passwd,
                    "auth[remember]": "on",
                    "auth[login]": 1,
                },
                )

        # TODO: Check that login attempt succeeded
        self.logged_in = True

    def get_saved_properties(self):
        if self.logged_in:
            resp = self.session.get(
                    "https://www.daft.ie/my-daft/saved-ads/",
                    headers=H_COMMON,
                    )

            soup = BeautifulSoup(resp.text, "html.parser")
            grid = soup.find(**{'class': 'saved-ads-grid'})
            return [
                    prop
                    for prop in grid.find_all('li')
                    if 'empty' in prop['class']
                    ] if grid else []

    def update_counties(self):
        key = "dp:counties"
        resp = self.session.get(
                "https://daft.ie/searchsale.daft",
                headers=H_COMMON
                )

        soup = BeautifulSoup(resp.text, "html.parser")
        results = {op['value']: op.text.strip()
                for op in soup.find("form").find("select").find_all("option")
                if op['value']}
        self.redis.hmset(key, results)

        return results

    def update_areas(self, county_code):
        key = "dp:counties:{}".format(county_code)
        payload = {
                    "cc_id": county_code,
                    "search_type": "sale",
                    "clean": 1,
                    }

        # NB: For some reason, this only works if you run the request twice?
        _ = self.session.post("https://daft.ie/sales/getAreas/",  data=payload, headers=H_AJAX)
        resp = self.session.post("https://daft.ie/sales/getAreas/",  data=payload, headers=H_AJAX)

        soup = BeautifulSoup(resp.text, "html.parser")
        areas = soup.find_all("span", **{'class': "multi-select-item-large"})

        def get_area_data(r):
            try:
                code = r.parent['for'].split('_')[-1]
                label = re.split("\s\(\d*\)$", r.text)[0]
                return code, label
            except TypeError as e:
                return

        area_data = dict(get_area_data(r) for r in areas)
        self.redis.hmset("dp:areas", area_data)

        results = area_data.keys()
        self.redis.lpush(key, *results)

        return results

    def search(self, county_code, area_code, property_type, sha):
        stats = RegionStats.from_code(self.redis, sha)
        search_source = PROPERTY_TYPES[property_type]['searchSource']
        pt_id = PROPERTY_TYPES[property_type]['pt_id']

        next_page = "http://www.daft.ie/search{}.daft".format(search_source)

        payload = {
                's[cc_id]': county_code,
                'sale_tab_name': '',
                's[area_type]': 'on',
                's[college_id]': '',
                's[a_id][]': area_code,
                's[mnp]': '',
                's[mxp]': '',
                's[mnb]': '',
                's[mxb]': '',
                's[mnbt]': '',
                's[mxbt]': '',
                's[days_old]': '',
                's[advanced]': 1,
                's[pt_id][]': pt_id,
                's[house_type]': '',
                's[new]': '',
                's[txt]': '',
                's[address]': '',
                'searchSource': search_source,
                'search': 1,
                }

        properties = []
        while True:
            resp = self.session.get(next_page, params=payload, headers=H_COMMON)
            if payload:
                payload = None # Only the first request needs search params
                stats.url = resp.url

            soup = BeautifulSoup(resp.text, "html.parser")

            # Scrape list of urls
            counters = soup.find_all(**{'class': "sr_counter"})
            hrefs = [counter.parent.a['href'] for counter in counters]
            property_urls = [urljoin("http://www.daft.ie/", href) for href in hrefs]
            properties.extend(self.register_properties(property_urls))

            # Find next page of results
            try:
                href = soup.find(**{'class': "next_page"}).a['href']
            except:
                break
            next_page = urljoin("http://www.daft.ie/", href)

        stats.current = properties
        return properties

    @property
    def counties(self):
        return County.get_all(self.redis)

    def get_property_code(self, url):
        path = urlsplit(url).path
        return re.search("(\d*?)/$", path).group(1)

    def register_properties(self, property_urls):
        property_map = {self.get_property_code(url): url for url in property_urls}
        for code, url in property_map.iteritems():
            key = "dp:properties:{}:url".format(code)
            self.redis.set(key, url)

        return property_map.keys()

    def update_property(self, property_code):
        prop = Property.from_code(self.redis, property_code)

        resp = self.session.get(prop.url)
        soup = BeautifulSoup(resp.text, "html.parser")

        prop.address = soup.find(id="address_box").h1.text.strip()
        prop.set_price(soup.find(id="smi-price-string").text)

        ber = soup.find(**{'class':"ber-hover"})
        if ber:
            prop.ber = ber.find('img')['alt']

        # TODO: Scrape more relevant info here!
