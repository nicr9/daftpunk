from requests import get as req_get
from urlparse import urlsplit, urljoin
from bs4 import BeautifulSoup
from pika import BlockingConnection, ConnectionParameters
from re import search
from json import dumps as json_dumps

RABBIT_QUEUE = 'daftpunk'

class DpScraper(object):
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

    def open_channel(self):
        conn = BlockingConnection(ConnectionParameters('localhost'))
        channel = conn.channel()
        channel.queue_declare(queue=RABBIT_QUEUE)

        return channel

    def process_url(self, url):
        # Get prop_id
        url_match = search("/(\d*)/?", url)
        prop_id = url_match.group(1)

        # Get prop_html
        resp = req_get(url)
        prop_html = resp.text

        return json_dumps([prop_id, prop_html])

    def run(self):
        channel = self.open_channel()

        for query in self.config['queries']:
            for url in self.find_properties(query):
                message = self.process_url(url)
                print message
                channel.basic_publish(
                        exchange='',
                        routing_key=RABBIT_QUEUE,
                        body=message,
                        )

        channel.close()

if __name__ == "__main__":
    config = {
            'queries': [
                'http://www.daft.ie/kildare/houses-for-sale/johnstownbridge/',
                ]
            }
    DpScraper(config)
