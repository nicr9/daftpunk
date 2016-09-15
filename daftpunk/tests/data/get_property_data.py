# -*- coding: utf-8 -*-

import bs4
import requests
import urlparse
import urllib


def get_gps_coordinates(number, street):
	pass


class PropertySummary(object):
	
	"""
		Describes the information we want about the property
	"""

	def get_header(self, soup):
	
		relative = soup.find("h2").find("a").attrs["href"].encode("ascii", "ignore")
		blurb = soup.find("h2").find("a").text.encode("ascii", "ignore").strip()
		
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

		self.link    = urlparse.urljoin("http://www.daft.ie", relative)
		self.daft_id = relative.strip("/").split("/")[-1].split("-")[-1]


	def get_price(self, soup):
		
		string_price = soup.find(
				"strong", attrs={"class": "price"}
			).text.encode("ascii", "ignore").replace(",", "")

		try:
			self.price = float(string_price)
		
		except ValueError:
			self.price = string_price

	def get_info(self, soup):	

		info = [ 
			item.text.encode("ascii", "ignore").strip().strip("|") 
			for item in soup.find("ul", attrs={"class": "info"}).find_all("li")
		]

		self.property_type = info[0]
		self.bedrooms      = int(info[1].split(" ")[0])
		self.bathrooms     = int(info[2].split(" ")[0])

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


class DaftResults(object):

	def __init__(self, location="dublin", offer="houses-for-sale"):
		
		self.target = urlparse.urljoin(
			"http://www.daft.ie", 
			"{}/{}".format(location, offer)
		)
		
		self.offset  = 0
		self.results = []
		self.gather_results()
		

	def is_property_summary(self, suspected_property):
		return suspected_property.find("h2") is not None

	def has_results(self, page):
		return page.find("div", attrs={"id": "gc_content"}) is None

	def get_next_page(self):

		params = {"offset" : self.offset}
		qstr = urllib.urlencode(params)
		response = requests.get("{}?{}".format(self.target, qstr))
		self.offset += 10

		return bs4.BeautifulSoup(response.content, "html.parser")

	def gather_results(self):

		page = self.get_next_page() 

		while self.has_results(page):

			# get all property summaries on the page
			items = page.find_all("div", attrs={"class": "box"})

			for item in items:
				if self.is_property_summary(item):
					self.results.append(PropertySummary(item))

			page = self.get_next_page()


if __name__ == "__main__":

	daft = DaftResults()

	for d in daft.results:
		print "{}\n".format(d.to_string())