import requests
import re
from bs4 import BeautifulSoup

from dp2 import H_AJAX, H_COMMON, H_FORM


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

            soup = BeautifulSoup(resp.text, "html")
            grid = soup.find(**{'class': 'saved-ads-grid'})
            return [
                    prop
                    for prop in grid.find_all('li')
                    if 'empty' in prop['class']
                    ] if grid else []

    @property
    def counties(self):
        key = "dp:counties"
        if self.redis.exists(key):
            results = self.redis.hgetall(key)
        else:
            resp = self.session.get("https://daft.ie/searchsale.daft", headers=H_COMMON)
            soup = BeautifulSoup(resp.text, "html")
            results = {op['value']: op.text.strip()
                    for op in soup.find("form").find("select").find_all("option")
                    if op['value']}
            self.redis.hmset(key, results)

        return results

    def get_county_label(self, county_code):
        key = "dp:counties"
        if self.redis.exists(key):
            results = self.redis.hget(key, county_code)
        else:
            results = self.counties[key]

        return results

    def get_region_codes(self, county_code):
        counties = self.counties
        if county_code not in counties:
            return

        key = "dp:counties:{}".format(county_code)
        if self.redis.exists(key):
            results = self.redis.lrange(key, 0, -1)
        else:
            payload = {
                        "cc_id": county_code,
                        "search_type": "sale",
                        "clean": 1,
                        }

            # NB: For some reason, this only works if you run the request twice?
            _ = self.session.post("https://daft.ie/sales/getAreas/",  data=payload, headers=H_AJAX)
            resp = self.session.post("https://daft.ie/sales/getAreas/",  data=payload, headers=H_AJAX)

            soup = BeautifulSoup(resp.text, "html")
            regions = soup.find_all("span", **{'class': "multi-select-item-large"})

            def get_region_data(r):
                try:
                    code = r.parent['for'].split('_')[-1]
                    label = re.split("\s\(\d*\)$", r.text)[0]
                    return code, label
                except TypeError as e:
                    return

            region_data = dict(get_region_data(r) for r in regions)
            self.redis.hmset("dp:regions", region_data)

            results = region_data.keys()
            self.redis.lpush(key, *results)

        return results

    def get_region_label(self, region_code):
        return self.redis.hget("dp:regions", region_code)

    def translate_regions(self, region_codes):
        return {code: self.get_region_label(code) for code in region_codes}

    def search(self, county_code, region, property_type):
        pass
