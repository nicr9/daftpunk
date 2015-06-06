from requests import get as req_get
from urlparse import urlsplit, urljoin
from bs4 import BeautifulSoup
from pika import BlockingConnection, ConnectionParameters
from re import search
from json import dumps as json_dumps
from time import time

RABBIT_QUEUE = 'daftpunk'

class DpSearcher(object):
    def __init__(self, config):
        self.config = config
        self.run()

    def reletive_url(self, href):
        return urljoin("http://%s" % self.host, href)

    def scrape_properties(self, soup):
        counters = soup.find_all(**{'class': "sr_counter"})
        hrefs = [counter.parent.a['href'] for counter in counters]

        return [self.reletive_url(href) for href in hrefs]

    def find_properties(self, search_url):
        self.host = urlsplit(search_url).netloc

        next_page = search_url
        properties = []
        while True:
            req = req_get(next_page)
            soup = BeautifulSoup(req.text)
            properties.extend(self.scrape_properties(soup))

            # Find next page of results
            try:
                href = soup.find(**{'class': "next_page"}).a['href']
            except:
                break
            next_page = self.reletive_url(href)

        return properties

    def rabbit_connect(self):
        conn = BlockingConnection(ConnectionParameters('localhost'))
        self.rabbit = conn.channel()
        self.rabbit.queue_declare(queue=RABBIT_QUEUE)

    def create_message(self, url):
        # Get prop_html
        resp = req_get(url)
        prop_html = resp.text

        timestamp = time()
        return json_dumps([url, timestamp, prop_html])

    def run(self):
        self.rabbit_connect()

        for query in self.config.queries:
            for url in self.find_properties(query):
                print url
                message = self.create_message(url)
                self.rabbit.basic_publish(
                        exchange='',
                        routing_key=RABBIT_QUEUE,
                        body=message,
                        )

        self.rabbit.close()

if __name__ == "__main__":
    from daftpunk import get_config
    DpSearcher(get_config())
