# -*- coding: utf-8 -*-

import os
import pickle
import datetime 

from lxml     import html
from urlparse import urlparse

from daftpunk.results import SummaryResultPages
from daftpunk.results import HttpResponseIterator


def get_datestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d')


def save_html(content, path):
    with open(path, "wb") as fp:
        fp.write(content)


def read_html(path):
    with open(path, "rb") as fp:
        return html.fromstring(fp.read())


def pickler(obj, path):
    with open(path, "wb") as fp:
        pickle.dump(obj, fp)


def unpickler(path):
    with open(path, "rb") as fp:
        return pickle.load(fp)


def directories(path, absolute=False):
    return [
        os.path.join(path, d) if absolute else d
        for d in os.listdir(path)
        if os.path.isdir(os.path.join(path, d))
    ]


def files(path, absolute=False):
    return [
        os.path.join(path, f) if absolute else f 
        for f in os.listdir(path) 
        if os.path.isfile(os.path.join(path, f))
    ]


class MockResults(object):

    date = None

    @staticmethod
    def get_data_path():
        return os.path.join(os.getcwd(), "tests/data")

    @staticmethod
    def set_earliest_date():
        MockResults.date = MockResults.get_dates()[0]

    @staticmethod
    def get_dates():
        return directories(MockResults.get_data_path())

    @staticmethod
    def get_date_path():
        return os.path.join(
            MockResults.get_data_path(), MockResults.date)

    @staticmethod
    def reconstruct_uri(file):
        if os.path.exists(file):
            elements = os.path.basename(file).split("_")
            query = elements[-1]
            path  = "/".join(elements[:-1])
            return "http://www.daft.ie/{}?{}".format(path, query)
        return None

    @staticmethod
    def file_path(path, url):
        parts    = urlparse(url)
        query    = parts.query
        endpoint = parts.path[1:].replace("/", "_")
        filename = "{}_{}".format(endpoint, query)
        return os.path.join(path, filename)

    @staticmethod
    def register_paths(test_adapter):
    
        data_path = MockResults.get_date_path()
        results   = files(data_path, absolute=True)
        
        no_results = results.pop(
            results.index(os.path.join(data_path, "no_results")))

        for file in results:
            uri = MockResults.reconstruct_uri(file)
            print "registering URI {}".format(uri)
            content = unpickler(file)  # create a callback with binary data
            print type(content)
            print content.content
            test_adapter.register_uri(
                "GET", uri, content=content, status_code=200)

    @staticmethod
    def get(*args, **kwargs):
        
        uri = args[0]
        
        data_path  = MockResults.get_date_path()
        data_files = files(data_path, absolute=True)
        
        no_results = os.path.join(data_path, "no_results")
        file       = MockResults.file_path(data_path, uri)

        if os.path.isfile(file):
            return unpickler(file)
        else:
            return unpickler(no_results)


def get_results_pages(county, offer, area):

    date = get_datestamp()
    path = os.path.join(os.getcwd(), "tests/data/{}".format(date))
    
    if not os.path.isdir(path): os.makedirs(path)

    results = SummaryResults(
        county=county, 
        offer=offer, 
        area=area, 
        mode="response"   # get the raw response so that we can replace 
                          # when mocking the requestst
    )

    offset  = 0

    print "\n-----"
    print "County : {}".format(county)
    print "Offer  : {}".format(offer)
    print "Area   : {}".format(area)

    print "Gathering results for : {}".format(results.target)

    for offset, url, page in HttpResponseIterator(results):
        
        out  = mock_file_mangler(path, url)
        
        print ">> URL is - '{}'".format(url)

        if not os.path.isfile(out):
        
            print ">> Grab it ..."      
            print ">> Save    - '{}'".format(out)

        else: 

            print "Got it already ..."

        pickler(page, out)

    offset += 10

    url  = results.get_page_url(offset)
    page = results.get_soup(url)

    outfile = os.path.join(path, "no_results")

    pickler(page, outfile)
    print "\n-----"


def gather_test_data():

    county   = "dublin"
    for_sale = "property-for-sale"
    new_home = "new-homes-for-sale" 

    areas = [
        "walkinstown", 
        "rathmines", 
        "rathfarnham", 
        "terenure", 
        "churchtown",
        "cherrywood",
    ]

    for area in areas:
        get_results_pages(county, for_sale, area)
        get_results_pages(county, new_home, area)


if __name__ == "__main__":

    gather_test_data()
