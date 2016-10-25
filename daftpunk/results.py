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


class PageIterator(object):

    def __init__(self, parent, url=False, offset=False):

        self.parent = parent
        self.offset = 0

        self.get_url    = url
        self.get_offest = offset

    def __iter__(self):
        return self

    def to_return(self, offset, url, page):
        
        data = []

        if self.get_offest:
            data.append(offset)
        if self.get_url:
            data.append(url)

        if data:
            data.append(page)
            return tuple(data)
        else:
            return page

    def next(self):
        
        offset = self.offset
        url    = self.parent.get_page_url(self.offset)
        page   = self.parent.get_me_stuff(url)

        if self.parent.is_paginated(page):
            if self.parent.has_results(page):
                self.offset += 10
                return self.to_return(offset, url, page)
            else:   
                raise StopIteration()   
        else:
            if offset < 10:
                self.offset += 10
                return self.to_return(offset, url, page)
            else:
                raise StopIteration()


class DaftSummaryResults(object):

    def __init__(self, **kwargs):

        self.set_target(**kwargs)
        self.set_mode(**kwargs)

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

    def set_mode(self, **kwargs):

        mode  = kwargs.get("mode", "soup")
        modes = "soup", "response"

        if mode not in modes:
            error = "'{}' is not a valid mode, pick one of these '{}'"
            raise ValueError(error.format(mode, modes))

        self.mode = mode

    def iterator(self, offest=False, url=False):
        return PageIterator(self, offest, url)

    def ensure_is_soup(self, item):
        if not isinstance(item, bs4.BeautifulSoup):
            return bs4.BeautifulSoup(item.content, "html.parser")
        return item
    
    def is_paginated(self, item):
        soup = self.ensure_is_soup(item)
        ul = soup.find("ul", attrs={"class": "paging clear"})
        if ul is not None:
            print ul.prettify()
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

    def get_me_stuff(self, url):

        response = requests.get(url)
        stuff    = None

        if self.mode == "soup":
            stuff = bs4.BeautifulSoup(response.content, "html.parser")
        elif self.mode == "response":
            stuff = response

        return stuff

#
# These are the different types of properties we can scrape summary info
# from on the Daft site. By manipulating the paths and endpoints we 
# can scrape relevant info.
#
# http://www.daft.ie/ireland
#

class PropertyForSaleSummaryParser(object):
    
    """
    ProprtyForSaleSummaryParser encapsulates all of the data we want to 
    extract from a Daft summary page for the property-for-sale path 
    in the Daft REST API.
    """

    def get_header(self, soup):
    
        relative = soup.find(
            "h2").find("a").attrs["href"].encode("ascii", "ignore")
        blurb = soup.find(
            "h2").find("a").text.encode("ascii", "ignore").strip()
        
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


class NewHomesForSaleSummaryParser(object):

    def __init__(self):
        pass


def get_summary_data(results, parser):
    return [parser(result) 
            for result in ResultsIterator(page) 
            for page in results.iterator()]
