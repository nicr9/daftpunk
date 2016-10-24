# -*- coding: utf-8 -*-

import urllib
import pytest
import requests

from mock_requests import MockRequests

from daftpunk.results import PropertySummaryParser

from daftpunk.results import DaftSummaryPageIterator
from daftpunk.results import DaftSummaryResults


requests = MockRequests


def get_offset_endpoint(url, offset):

	params = {"offset" : offset}
	qstr = urllib.urlencode(params)
	return "{}?{}".format(url, qstr)


def _test_page_iteration(results):

	sales = "http://www.daft.ie/dublin/houses-for-sale/walkinstown" 
	assert results.target == sales

	endpoint = get_offset_endpoint(sales, 10)
	url = results.get_page_url(10)
	assert url == endpoint

	stuff = results.get_me_stuff(url)
	assert results.has_results(stuff)

	endpoint = get_offset_endpoint(sales, 10000)
	url = results.get_page_url(10000)
	assert url == endpoint

	stuff = results.get_me_stuff(url)
	assert not results.has_results(stuff)

	for offest, url, page in results.iterator():
		assert results.has_results(page)


def test_page_iteration_for_soup():

	results = DaftSummaryResults(
		county="dublin",
		area="walkinstown",
		mode="soup"
	)
	assert results.mode == "soup"
	
	_test_page_iteration(results)


def test_page_iteration_for_response():

	results = DaftSummaryResults(
		county="dublin",
		area="walkinstown",
		mode="response"
	)
	assert results.mode == "response"

	_test_page_iteration(results)



def test_page_parsing():

	results = DaftSummaryResults(
		county="dublin",
		area="walkinstown",
		mode="soup"
	)

	url  = results.get_page_url(10)
	page = results.get_me_stuff(url)
	
	assert results.has_results(page)

	results.
