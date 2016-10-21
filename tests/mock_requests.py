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
        
        self.path  = os.path.join(os.getcwd(), "tests/data")
        self.dates = directories(self.path, absolute=True)
 
        self.current_date = 0

    def how_many_dates(self):
        return len(self.dates)

    def get_date(self):
        return self.dates[self.date_idx]

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


def gather_daft_summary_results_pages():

    date = get_datestamp()
    path = os.path.join(
        os.getcwd(), "tests/data/{}".format(date))
    
    if not os.path.isdir(path): os.makedirs(path)

    results = DaftSummaryResults(
        county="dublin", area="walkinstown", mode="response")

    offset  = 0

    for offset, url, page in results.iterator():
        
        outfile  = mock_file_mangler(path, url)
        
        print ">> URL is - '{}'".format(url)

        if not os.path.isfile(outfile):
        
            print ">> Grab it ..."      
            print ">> Save    - '{}'".format(outfile)

        else: 

            print "Got it already ..."

        pickler(page, outfile)

    offset += 10

    url  = results.get_page_url(offset)
    page = results.get_me_stuff(url)

    outfile = os.path.join(path, "no_results")

    pickler(page, outfile)


if __name__ == "__main__":

    gather_daft_summary_results_pages()