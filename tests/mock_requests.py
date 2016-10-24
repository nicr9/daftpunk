# -*- coding: utf-8 -*-

import os
import pickle
import datetime 

from lxml     import html
from urlparse import urlparse
from mock     import MagicMock

from daftpunk.results import DaftSummaryResults


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


def mock_file_mangler(path, url):
    parts    = urlparse(url)
    query    = parts.query
    endpoint = parts.path[1:].replace("/", "_")
    filename = "{}_{}".format(endpoint, query)
    return os.path.join(path, filename)


def MockRequests(MagicMock):

    def __init__(self):
        
        super(MockRequests, self).__init__()

        self.path  = os.path.join(os.getcwd(), "tests/data")
        self.dates = directories(self.path, absolute=True)
 
        self.current_date = 0

    def how_many_dates(self):
        return len(self.dates)

    def get_date(self):
        return self.dates[self.date_idx]
    
    def set_date(self, date):
        self.current_date = date

    def next_date(self):
        self.current_date +=1

    def get(self, url, *args, **kwargs):

        date     = self.get_date()
        results  = files(date) 
        filename = mock_file_mangler(date, url) 

        no_results = results.pop("no_results")

        if filename in results:
            return unpickler(
                os.path.join(date, filename))
        else:
            return unpickler(
                os.path.join(data, no_results))


def get_results_pages(county, offer, area):

    date = get_datestamp()
    path = os.path.join(
        os.getcwd(), "tests/data/{}".format(date))
    
    if not os.path.isdir(path): os.makedirs(path)

    results = DaftSummaryResults(
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

    for offset, url, page in results.iterator():
        
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
    page = results.get_me_stuff(url)

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
