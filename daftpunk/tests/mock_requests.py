# -*- coding: utf-8 -*-

import os
import pickle 

from mock import MagicMock

from daftpunk.results import DaftSummaryResultPages


def pickler(obj, path):
    with open(path, "wb") as fp:
        pickle.dump(obj, fp)


def unpickler(path):
    with open(path, "rb") as fp:
        return pickle.load(fp)


def files(path, absolute=False):
    return [
        os.path.join(path, f) if absolute else f 
        for f in os.listdir(path) 
        if os.path.isfile(os.path.join(path, f))]


def MockRequests(MagicMock):

    def __init__(self):
        
        path = os.path.join(os.get_cwd(), "data")

        self.mock_get_responses = {}
        self.no_results = None

        for pkl in files(path):
            pkl_path = os.path.join(path, pkl)
            if pkl.startswith("http://"):
                self.mock_get_responses[pkl] = unpickler(pkl_path)
            elif pkl.startswith("no_results"):
                self.no_results = unpickler(pkl_path)

    def get(self, url):
        
        if url in self.mock_get_responses:
            return self.mock_get_responses[url]
        else:
            return self.no_results


def gather_daft_summary_results_pages():

    path = os.path.join(os.get_cwd(), "data")
    
    for page in DaftSummaryResultPages():
        pickler(
            page, 
            os.path.join(path, page.get_page_url())
        )


if __name__ == "__main__":

    gather_daft_summary_results_pages()