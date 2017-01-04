# -*- coding: utf-8 -*-

import os
import pickle
import datetime

from lxml     import html
from urlparse import urlparse

from daftpunk.results import SummaryResultPages
from daftpunk.results import HttpResponseIterator


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


def dates():
    path = os.path.join(os.getcwd(), "tests/data")
    for root, dirs, _ in os.walk(path):
        for d in dirs:
            yield os.path.join(root, d)

class MockResults(object):
    def __init__(self, date):
        self.date_path = os.path.join(MockResults.path, MockResults.date)

    @staticmethod
    def set_earliest_date():
        MockResults.date = MockResults.get_dates()[0]

    @staticmethod
    def get_dates():
        return directories(MockResults.path)

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

def mock_get(uri, *args, **kwargs):
    data_path = dates().next()
    no_results = os.path.join(data_path, "no_results")
    file       = MockResults.file_path(data_path, uri)

    if os.path.isfile(file):
        return unpickler(file)
    else:
        return unpickler(no_results)


def get_results_pages(county, offer, area):
    # Create folder for today's data
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    path = os.path.join(os.getcwd(), "tests/data/{}".format(date))
    if not os.path.isdir(path): os.makedirs(path)

    results = SummaryResultPages(
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

    for offset, url, response in HttpResponseIterator(results):
        out  = MockResults.file_path(path, url)

        print ">> URL is - '{}'".format(url)

        if not os.path.isfile(out):

            print ">> Grab it ..."
            print ">> Save    - '{}'".format(out)

        else:

            print "Got it already ..."

        pickler(response, out)

    offset += 10

    url      = results.get_page_url(offset)
    response = results.get_response(url)

    out = os.path.join(path, "no_results")

    pickler(response, out)
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
