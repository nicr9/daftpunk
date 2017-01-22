# -*- coding: utf-8 -*-

import urllib
import pytest
import requests

from mock_results import mock_get, dates

from daftpunk.results import SummaryResultPages
from daftpunk.results import PageIterator

from daftpunk.results import get_properties_for_sale
from daftpunk.results import get_new_homes_for_sale


class TestResults(object):
    def setup(self):
        requests.get = mock_get

    def __get_offset_endpoint(self, url, offset):
        params = {"offset" : offset}
        qstr = urllib.urlencode(params)
        return "{}?{}".format(url, qstr)

    def __test_page_iteration(self, results):

        sales = "http://www.daft.ie/dublin/property-for-sale/walkinstown"
        assert results.target == sales

        endpoint = self.__get_offset_endpoint(sales, 10)
        url = results.get_page_url(10)
        assert url == endpoint

        soup = results.get_soup(url)
        assert results.has_results(soup)
        assert results.is_paginated(soup)

        endpoint = self.__get_offset_endpoint(sales, 10000)
        url = results.get_page_url(10000)
        assert url == endpoint

        soup = results.get_soup(url)
        has_results = results.has_results(soup)
        is_paginated = results.is_paginated(soup)

        assert not has_results
        assert not is_paginated

        for page in PageIterator(results):
                assert results.has_results(page)

    def test_page_iteration_for_soup(self):
        results = SummaryResultPages(
                county="dublin",
                offer="property-for-sale",
                area="walkinstown"
        )
        self.__test_page_iteration(results)

    def __check_number_offered(self, county, offer, area, expected):
        offers = {
                "property-for-sale"  : get_properties_for_sale,
                "new-homes-for-sale" : get_new_homes_for_sale,
        }

        assert offer in offers

        results = SummaryResultPages(
                county=county, offer=offer, area=area)

        actual = len(offers.get(offer)(results))

        assert actual == expected, "{}/{}/{}".format(county, offer, area)

    def test_property_for_sale_page_parsing(self):
        for date in dates():
            print "Date : {}".format(date)

            offer = "property-for-sale"

            test_areas = [
                    ("dublin", "rathmines",   22),
                    ("dublin", "walkinstown", 21),
                    ("dublin", "rathfarnham", 71),
                    ("dublin", "terenure",    28),
                    ("dublin", "churchtown",  15),
                    ("dublin", "cherrywood",   0),
            ]

            for county, area, number in test_areas:
                    self.__check_number_offered(county, offer, area, number)

    def test_new_homes_for_sale_page_parsing(self):
        for date in dates():
            print "Date : {}".format(date)

            offer = "new-homes-for-sale"

            test_areas = [
                    ("dublin", "rathmines",   1),
                    ("dublin", "walkinstown", 1),
                    ("dublin", "rathfarnham", 3),
                    ("dublin", "terenure",    1),
                    ("dublin", "churchtown",  1),
                    ("dublin", "cherrywood",  0),
            ]

            for county, area, number in test_areas:
                    self.__check_number_offered(county, offer, area, number)
