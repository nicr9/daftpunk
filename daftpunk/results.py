# -*- coding: utf-8 -*-

import os
import re
import bs4
import urllib
import urlparse
import requests


def get_gps_coordinates(number, street):
    pass


class DaftSummaryResultsIterator(object):

    def __init__(self, parent):

        self.parent = parent
        self.offset = 0

    def __iter__(self):
        return self

    def next(self):
        
        url  = self.parent.get_page_url(self.offset)
        page = self.parent.get_me_stuff(url)

        if self.parent.has_results(page):
            self.offset += 10
            return self.offset, url, page
        else:
            raise StopIteration()


class DaftSummaryPageIterator(object):

    def __init__(self, page):
        self.items = page.find_all("div", attrs={"class": "box"})

    def __iter__(self):
        return self

    def next(self):

        try:
            item = self.items.pop(0)
            while item.find("h2") is None:
                item = self.items.pop(0)
            return item

        except IndexError:
            raise StopIteration()


class DaftSummaryResults(object):

    def __init__(self, **kwargs):

        self.set_target(**kwargs)
        self.set_mode(**kwargs)

    def set_target(self, **kwargs):

        # Results page settings, use defaults

        county = kwargs.get("county", "ireland")
        offer  = kwargs.get("offer",  "houses-for-sale")
        area   = kwargs.get("area",    None)

        path = os.path.join(county, offer)

        if area is not None:
            path = os.path.join(path, area)

        self.target = urlparse.urljoin("http://www.daft.ie", path)

    def set_mode(self, **kwargs):

        mode  = kwargs.get("mode", "soup")
        modes = "soup", "response"

        if mode not in modes:
            error = "'{}' is not a valid mode, pick one of these '{}'"
            raise ValueError(error.format(mode, modes))

        self.mode = mode

    def iterator(self):
        return DaftSummaryResultsIterator(self)

    def has_results(self, item):
        soup = None
        if not isinstance(item, bs4.BeautifulSoup):
            soup = bs4.BeautifulSoup(item.content, "html.parser")
        else:
            soup = item
        return soup.find("div", attrs={"id": "gc_content"}) is None
        
    def get_page_url(self, offset):
        params = {"offset" : offset}
        qstr = urllib.urlencode(params)
        endpoint = "{}?{}".format(self.target, qstr)
        return endpoint

    def get_me_stuff(self, url):
        
        response = requests.get(url)
        print response
        stuff    = None

        if self.mode == "soup":
            stuff = bs4.BeautifulSoup(response.content, "html.parser")
        elif self.mode == "response":
            stuff = response

        return stuff


class PropertySummaryParser(object):
    
    """
        Describes the information we want about the property
    """

    def get_header(self, soup):
    
        relative = soup.find("h2").find("a").attrs["href"].encode("ascii", "ignore")
        blurb = soup.find("h2").find("a").text.encode("ascii", "ignore").strip()
        
        print blurb 

        addr, ptype = blurb.split(" - ")
        
        addr = addr.strip()
        ptype = ptype.strip()

        if ptype == "New Development":
            parts = [x.strip() for x in addr.split(",")[1:]]
            self.address = ", ".join(parts)
            self.new_development = "Yes"
        else:
            self.address = addr
            self.new_development = "No"

        print "\n---"
        print self.address

        self.link    = urlparse.urljoin("http://www.daft.ie", relative)
        self.daft_id = relative.strip("/").split("/")[-1].split("-")[-1]


    def get_price(self, soup):
        
        string_price = soup.find(
                "strong", attrs={"class": "price"}
            ).text.encode("ascii", "ignore").replace(",", "")

        print string_price

        try:
            self.price = float(string_price)
        
        except ValueError:
            self.price = string_price

    def get_info(self, soup):   

        info = [ 
            item.text.encode("ascii", "ignore").strip().strip("|") 
            for item in soup.find("ul", attrs={"class": "info"}).find_all("li")
        ]

        print info
        print "---\n"

        self.property_type = info[0]

        if len(info) == 3:

            self.property_type = info[0]
            self.bedrooms      = int(info[1].split(" ")[0])
            self.bathrooms     = int(info[2].split(" ")[0])

        else:
            
            self.property_type = info[0]
            
            string = " ".join(info)
            beds   = re.compile(r"\d+ Beds")
            baths  = re.compile(r"\d+ Baths")
             
            has_beds = re.search(beds, string)
            has_baths = re.search(baths, string)

            self.bedrooms  = None if has_beds  is None else has_beds.group().split(" ")[0]
            self.bathrooms = None if has_baths is None else has_baths.group().split(" ")[0]


    def get_ber(self, soup):

        self.ber = None

        rating = soup.find("span", attrs={"ber-hover"})
        
        if rating is not None:
            self.ber = rating.find("img").attrs["alt"].encode("ascii", "ignore").split(" ")[-1]

    def get_agent(self, soup):
        
        self.estate_agent = None 

        tmp = soup.find("li", attrs={"class": "agent-name-link truncate"})

        if tmp is not None:
            self.estate_agent = tmp.find("a").text.encode("ascii", "ignore")

    def __init__(self, soup):

        self.get_header(soup)
        self.get_price(soup)
        self.get_info(soup)
        self.get_ber(soup)
        self.get_agent(soup)

        ## TODO use GoogleMaps API

    def to_string(self):
        return (
            "-----\n"
            "'Daft ID'         : '{}'\n"
            "'Address'         : '{}'\n"
            "'Price'           : '{}'\n"
            "'Type'            : '{}'\n"
            "'New Development' : '{}'\n"
            "'BER'             : '{}'\n"
            "'Bedrooms'        : '{}'\n"
            "'Bathrooms'       : '{}'\n"
            "'Agent'           : '{}'\n\n"
            "'Web Link' - '{}'\n"
            "-----\n"
        ).format(
            self.daft_id, self.address, self.price, self.property_type,
            self.new_development, self.ber, self.bedrooms, self.bathrooms,
            self.estate_agent, self.link
        )

def gather_summary_results(self):

    results = []

    for page in DaftSummaryResults():

        # get all property summaries on the page
        items = page.find_all("div", attrs={"class": "box"})

        for item in items:
            if DaftSummaryResultPages.is_property(item):
                results.append(PropertySummary(item))


    return results
