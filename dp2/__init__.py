import requests
import re
import sys

from bs4 import BeautifulSoup
from pprint import pprint
from urlparse import parse_qs, urlparse


def stats(resp):
    if resp.history:
        print("\n\033[94mHistory\033[0m")
        for redirect in resp.history:
            print("{}: {}".format(redirect.url, redirect.status_code))


    print("\n\033[94mGeneral\033[0m")
    print("Request URL: {}".format(resp.url))
    print("Request Method: {}".format(resp.request.method))
    print("Status Code: {}".format(resp.status_code))


    print("\n\033[94mResponse Headers\033[0m")
    for k, v in sorted(resp.headers.items(), key=lambda s: s[0].lower()):
        print("{}: {}".format(k, v))


    print("\n\033[94mRequest Headers\033[0m")
    for k, v in sorted(resp.request.headers.items(), key=lambda s: s[0].lower()):
        print("{}: {}".format(k, v))


    qs_params = parse_qs(urlparse(resp.url).query)
    if qs_params:
        print("\n\033[94mQuery String Parms\033[0m")
        for k, v in sorted(qs_params.items()):
            print("{}: {}".format(k, ', '.join(v)))

    print


H_COMMON = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36",
        }

H_AJAX = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        }


H_FORM = H_COMMON.copy()
H_FORM.update({
        "Content-Type": "application/x-www-form-urlencoded",
        })


class DaftClient(object):
    def __init__(self, user, passwd):
        self.session = requests.Session()
        self.login(user, passwd)
        self.get_counties()

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

        self.get_saved_properties(resp)

    def get_saved_properties(self, resp=None):
        if not resp:
            resp = self.session.get(
                    "https://www.daft.ie/my-daft/saved-ads/",
                    headers=H_COMMON,
                    )

        soup = BeautifulSoup(resp.text, "html")
        grid = soup.find(**{'class': 'saved-ads-grid'})
        self.saved = [prop for prop in grid.find_all('li') if 'empty' in prop['class']]

    def get_counties(self):
        resp = self.session.get("https://daft.ie/searchsale.daft", headers=H_COMMON)
        soup = BeautifulSoup(resp.text, "html")
        self.counties = {op.text.strip(): op['value']
                for op in soup.find("form").find("select").find_all("option")
                if op['value']}

    def get_regions(self, county):
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


class DP2(object):
    def __init__(self, username, password):
        self.client = DaftClient(username, password)

if __name__ == "__main__":
    dp = DP2(*sys.argv[1:3])
    pprint(dp.client.get_regions('Co. Kildare'))
