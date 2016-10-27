# -*- coding: utf-8 -*-

import os
import re
import bs4
import urllib
import urlparse
import requests


def get_gps_coordinates(number, street):
    pass


class ResultsIterator(object):

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


class BaseIterator(object):

    def __init__(self, results):

        self.results = results
        self.offset = 0

    def __iter__(self):
        return self

    def next(self):
        raise StopIteration()


class HttpResponseIterator(BaseIterator):

    def __init__(self, results):
        super(HttpResponseIterator, self).__init__(results)

    def next(self):

        offset   = self.offset
        url      = self.results.get_page_url(offset)
        response = self.results.get_response(url)

        if self.results.is_paginated(response):
            
            if self.results.has_results(response):
                self.offset += 10
                return offset, url, response
            else:   
                raise StopIteration()   
        else:
            if offset < 10:
                self.offset += 10
                return offset, url, response
            else:
                raise StopIteration()


class PageIterator(BaseIterator):

    def __init__(self, results):
        super(PageIterator, self).__init__(results)

    def next(self):
        
        offset = self.offset
        url    = self.results.get_page_url(self.offset)
        page   = self.results.get_soup(url)

        if self.results.is_paginated(page):
            if self.results.has_results(page):
                self.offset += 10
                return page
            else:   
                raise StopIteration()   
        else:
            if offset < 10:
                self.offset += 10
                return page
            else:
                raise StopIteration()


class SummaryResultPages(object):

    def __init__(self, **kwargs):
        self.set_target(**kwargs)

    def set_target(self, **kwargs):

        # Results page settings, use defaults

        county = kwargs.get("county", "")
        offer  = kwargs.get("offer",  "")
        area   = kwargs.get("area",   "")

        if not (county and offer):
            raise ValueError("You must supply a county and an offer type ...")

        path = os.path.join(county, offer)

        if area:
            path = os.path.join(path, area)

        self.target = urlparse.urljoin("http://www.daft.ie", path)

    def ensure_is_soup(self, item):
        if not isinstance(item, bs4.BeautifulSoup):
            return bs4.BeautifulSoup(item.content, "html.parser")
        return item
    
    def is_paginated(self, item):
        soup = self.ensure_is_soup(item)
        ul = soup.find("ul", attrs={"class": "paging clear"})
        return ul is not None and ul.find("li") is not None

    def has_results(self, item):
        
        soup = self.ensure_is_soup(item)
        div  = soup.find("div", attrs={"id": "gc_content"})

        if div is not None:
            no_results = div.find(
                "h1").text.encode("ascii", "ignore").strip().lower()
            return not (no_results == "no results")
        
        return True
        
    def get_page_url(self, offset):
        params = {"offset" : offset}
        qstr = urllib.urlencode(params)
        endpoint = "{}?{}".format(self.target, qstr)
        return endpoint

    def get_response(self, url):
        response = requests.get(url)
        return response

    def get_soup(self, url):
        content = self.get_response(url).content
        soup    = bs4.BeautifulSoup(content, "html.parser")
        return soup


#
# These are the different types of properties we can scrape summary 
# info from on the Daft site. By manipulating the paths and
# endpoints we can scrape relevant info.
#
# http://www.daft.ie/ireland
#

class SummaryParser(object):

    @staticmethod
    def parse_relative_path(soup):
        return soup.find("h2").find(
            "a").attrs["href"].encode("ascii", "ignore")
    
    @staticmethod
    def parse_full_ad_link(soup):
        relative = PropertyForSaleSummaryParser.parse_relative_path(soup)
        return urlparse.urljoin("http://www.daft.ie", relative)

    @staticmethod
    def parse_daft_id(soup):
        path = PropertyForSaleSummaryParser.parse_relative_path(soup)
        daft_id = path.strip("/").split("/")[-1].split("-")[-1]
        return daft_id

    @staticmethod
    def parse_blurb(soup):
        return soup.find("h2").find(
            "a").text.encode("ascii", "ignore").strip()

    @staticmethod
    def parse_address(soup):
        blurb = PropertyForSaleSummaryParser.parse_blurb(soup)
        return blurb.split("-")[0].strip()

    @staticmethod
    def parse_property_type(soup):
        blurb = PropertyForSaleSummaryParser.parse_blurb(soup)
        return blurb.split("-")[1].strip().lower()

    @staticmethod
    def parse_agent(soup):
        agent = soup.find("li", attrs={"class": "agent-name-link truncate"})
        if agent is not None:
            return agent.find("a").text.encode("ascii", "ignore")
        return None


    def __init__(self, soup):

        self.daft_link = self.parse_full_ad_link(soup)
        self.daft_id   = self.parse_daft_id(soup)
        self.address   = self.parse_address(soup)

        self.estate_agent  = self.parse_agent(soup)

    def to_string(self):
        return ""


class PropertyForSaleSummaryParser(SummaryParser):
    
    """
    PropertyForSaleSummaryParser encapsulates all of the data we 
    want to extract from a Daft summary page for the 
    property-for-sale path in the Daft REST API.
    """

    @staticmethod
    def is_new_development(soup):
        pt = PropertyForSaleSummaryParser.parse_property_type(soup)
        return pt == "new development"

    @staticmethod
    def parse_price(soup):
        
        string_price = soup.find(
                "strong", attrs={"class": "price"}
            ).text.encode("ascii", "ignore").replace(",", "")

        try:
            return float(string_price)
        
        except ValueError:
            return string_price
    
    @staticmethod
    def parse_property_details(soup):   

        info = [ 
            item.text.encode("ascii", "ignore").strip().strip("|") 
            for item in soup.find("ul", attrs={"class": "info"}).find_all("li")
        ]
        
        property_type = info[0]

        if property_type.startswith("Apartment"):
            property_type = "Apartment"

        bedrooms      = None
        bathrooms     = None

        if len(info) == 3:

            bedrooms      = int(info[1].split(" ")[0])
            bathrooms     = int(info[2].split(" ")[0])

        else:
            
            string = " ".join(info)
            beds   = re.compile(r"\d+ Beds")
            baths  = re.compile(r"\d+ Baths")
             
            has_beds = re.search(beds, string)
            has_baths = re.search(baths, string)

            bedrooms  = None if has_beds  is None else has_beds.group().split(" ")[0]
            bathrooms = None if has_baths is None else has_baths.group().split(" ")[0]

        return bedrooms, bathrooms, property_type

    @staticmethod
    def parse_ber(soup):
        rating = soup.find("span", attrs={"ber-hover"})
        if rating is not None:
            return rating.find("img").attrs["alt"].encode(
                "ascii", "ignore").split(" ")[-1]
        return None

    def __init__(self, soup):

        super(PropertyForSaleSummaryParser, self).__init__(soup)

        self.price     = self.parse_price(soup)
        self.ber       = self.parse_ber(soup)        
        
        self.bedrooms, self.bathrooms, self.property_type = \
            self.parse_property_details(soup)

        ## TODO use GoogleMaps API

    def to_string(self):
        return (
            "--- Property For Sale ---\n"
            "'Daft ID'         : '{}'\n"
            "'Address'         : '{}'\n"
            "'Price'           : '{}'\n"
            "'Type'            : '{}'\n"
            "'BER'             : '{}'\n"
            "'Bedrooms'        : '{}'\n"
            "'Bathrooms'       : '{}'\n"
            "'Agent'           : '{}'\n\n"
            "'Daft Link' - '{}'\n"
            "-----\n"
        ).format(
            self.daft_id, self.address, 
            self.price, self.property_type,
            self.ber, self.bedrooms, 
            self.bathrooms, self.estate_agent, 
            self.daft_link
        )


class PriceRange(object):

    def __init__(self, pfrom, pto):

        setattr(self, "from", pfrom)
        setattr(self, "to",   pto)

    def to_string(self):
        return "'{} - {}'".format(
            getattr(self, "from"), getattr(self, "to"))

    def __str__(self):
        return self.to_string()


class NewHomesForSaleSummaryParser(SummaryParser):

    @staticmethod
    def parse_price_range(soup):
        
        string_price = soup.find(
                "strong", attrs={"class": "price"}
            ).text.encode("ascii", "ignore").replace(",", "")

        if string_price == "Price on Application":
            return string_price
        else:
            parts = string_price.split(" ")
            pfrom = float(parts[1])
            pto   = float(parts[3])
            return PriceRange(pfrom, pto)

    def __init__(self, soup):
        
        super(NewHomesForSaleSummaryParser, self).__init__(soup)

        self.price_range = self.parse_price_range(soup)

    def to_string(self):
        return (
            "--- New Home For Sale ---\n"
            "'Daft ID'         : '{}'\n"
            "'Address'         : '{}'\n"
            "'Price Range'     : '{}'\n"
            "'Agent'           : '{}'\n\n"
            "'Daft Link' - '{}'\n"
            "-----\n"
        ).format(
            self.daft_id, self.address, 
            self.price_range, self.estate_agent, 
            self.daft_link
        )


def get_properties_for_sale(results):

    return [PropertyForSaleSummaryParser(result) 
            for page   in PageIterator(results)
            for result in ResultsIterator(page)]


def get_new_homes_for_sale(results):

    return [NewHomesForSaleSummaryParser(result) 
        for page   in PageIterator(results)
        for result in ResultsIterator(page)]