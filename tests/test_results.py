# -*- coding: utf-8 -*-

import urllib
import pytest
import requests

from mock_results import MockResults

from daftpunk.results import SummaryResultPages
from daftpunk.results import PageIterator

from daftpunk.results import get_properties_for_sale
from daftpunk.results import get_new_homes_for_sale


class TestResults(object):

	def setup(self):
		
		MockResults.set_earliest_date()
		requests.get = MockResults.get

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

		stuff = results.get_soup(url)
		assert results.has_results(stuff)

		endpoint = self.__get_offset_endpoint(sales, 10000)
		url = results.get_page_url(10000)
		assert url == endpoint

		stuff = results.get_soup(url)
		has_results = results.has_results(stuff)
		assert not has_results

		for page in PageIterator(results):
			assert results.has_results(page)
	
	def test_page_iteration_for_soup(self):

		results = SummaryResultPages(
			county="dublin",
			offer="property-for-sale",
			area="walkinstown"
		)
		self.__test_page_iteration(results)

	def __property_for_sale(self, county, area, expected_number):

		results = SummaryResultPages(
			county=county,
			offer="property-for-sale",
			area=area
		)

		url  = results.get_page_url(0)
		page = results.get_soup(url)
		
		has_results  = results.has_results(page)
		is_paginated = results.is_paginated(page)

		if has_results:
			assert is_paginated

		data = get_properties_for_sale(results)
		actual_number = len(data)

		assert actual_number == expected_number

	def test_property_for_sale_page_parsing(self):

		# Check positive cases

		print "Date : {}".format(MockResults.date)
		
		test_areas = [
			("dublin", "rathmines",   22),
			("dublin", "walkinstown", 21),
			("dublin", "rathfarnham", 71),
			("dublin", "terenure",    28),
			("dublin", "churchtown",  15),
			("dublin", "cherrywood",   0),
		]

		for county, area, expected_number in test_areas:
			self.__property_for_sale(county, area, expected_number)

	def test_new_homes_for_sale_page_parsing(self):

		results = SummaryResultPages(
			county="dublin", 
			offer="new-homes-for-sale",
			area="walkinstown"
		)

		url = results.get_page_url(0)
		page = results.get_soup(url)

		is_paginated = results.is_paginated(page)
		has_results  = results.has_results(page)
		assert not is_paginated
		assert has_results

		data = get_new_homes_for_sale(results)

		assert data
		assert len(data) == 1
