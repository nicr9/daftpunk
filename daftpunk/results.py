# -*- coding: utf-8 -*-

"""
    
"""

import re
import bs4
import urllib
import urlparse
import requests


def get_gps_coordinates(number, street):
    pass


class PropertySummary(object):
    
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


class DaftSummaryResultPages(object):

    def __init__(self, location="dublin", offer="houses-for-sale"):
        
        self.target = urlparse.urljoin(
            "http://www.daft.ie", 
            "{}/{}".format(location, offer)
        )
        
        self.offset  = 0

    def __iter__(self):
        return self
        
    @staticmethod
    def is_property(suspected_property):
        return suspected_property.find("h2") is not None

    @staticmethod
    def has_results(page):
        return page.find("div", attrs={"id": "gc_content"}) is None

    def get_page_url(self, offset):
        params = {"offset" : offset}
        qstr = urllib.urlencode(params)
        return "{}?{}".format(self.target, qstr)

    def get_soup(self, offset):
        response = requests.get(self.get_page_url())
        return bs4.BeautifulSoup(response.content, "html.parser")

    def next(self):

        if DaftSummaryResultPages.has_results():
            soup = self.get_soup(self.offset)
            self.offset += 10
            return soup
        else:
            raise StopIteration()


def gather_summary_results(self):

    results = []

    for page in DaftSummaryResultPages():

        # get all property summaries on the page
        items = page.find_all("div", attrs={"class": "box"})

        for item in items:
            if DaftSummaryResultPages.is_property(item):
                results.append(PropertySummary(item))


    return results