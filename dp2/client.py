import requests
import re
from bs4 import BeautifulSoup

from dp2 import H_AJAX, H_COMMON, H_FORM


class DaftClient(object):
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
        self.refresh()

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

    def refresh(self):
        self.counties = self.get_counties()

    def get_saved_properties(self):
        if self.logged_in
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

    def get_counties(self):
        resp = self.session.get("https://daft.ie/searchsale.daft", headers=H_COMMON)
        soup = BeautifulSoup(resp.text, "html")
        return {op.text.strip(): op['value']
                for op in soup.find("form").find("select").find_all("option")
                if op['value']}

    def get_regions(self, county):
        if not county in self.counties:
            return

        payload = {
                    "cc_id": self.counties[county],
                    "search_type": "sale",
                    "clean": 1,
                    }
        temp = payload.copy()

        # NB: For some reason, this only works if you run the request twice?
        _ = self.session.post("https://daft.ie/sales/getAreas/",  data=payload, headers=H_AJAX)
        resp = self.session.post("https://daft.ie/sales/getAreas/",  data=payload, headers=H_AJAX)

        soup = BeautifulSoup(resp.text, "html")
        regions = soup.find_all("span", **{'class': "multi-select-item-large"})
        return [re.split("\s\(\d*\)$", r.text)[0] for r in regions]
