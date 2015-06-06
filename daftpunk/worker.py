from pika import BlockingConnection, ConnectionParameters
from json import loads as json_loads
from redis import StrictRedis
from re import sub as re_sub
from re import match as re_match
from requests import get as req_get
from functools import partial
from daftpunk import GEOCODE_API, BER_RATINGS
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk import FreqDist
from urlparse import urlsplit
import logging
import traceback

RABBIT_QUEUE = 'daftpunk'

class DpWorker(object):
    def __init__(self, config):
        self.config = config
        self.run()

    def rabbit_connect(self, callback):
        conn = BlockingConnection(ConnectionParameters('localhost'))
        self.rabbit = conn.channel()
        self.rabbit.queue_declare(queue=RABBIT_QUEUE)
        self.rabbit.basic_consume(
                callback,
                queue=RABBIT_QUEUE,
                no_ack=True
                )


        print "connected"

    def run(self):
        def callback(parser, ch, method, properties, msg):
            prop_id = parser.process_message(msg)
            print " [x] Processed %s" % (prop_id,)

        parser = DpParser(self.config)
        self.rabbit_connect(partial(callback, parser))

        print ' [*] Waiting for messages. To exit press CTRL+C'
        self.rabbit.start_consuming()

def scrape_once(func):
    func.__scrape_once__ = True
    return func

def scrape_update(func):
    func.__scrape_update__ = True
    return func

class DpParser(object):
    def __init__(self, config):
        self.config = config
        self.redis = StrictRedis(host='localhost', port=6379, db=0)

    def scrape_all(self, url, timestamp, html):
        category, tag, id_ = self.strip_url(url)
        soup = BeautifulSoup(html)

        firsttime = not self.redis.sismember('daftpunk:properties', id_)

        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            try:
                if firsttime and hasattr(attr, '__scrape_once__'):
                    attr(id_, timestamp, soup)
                elif hasattr(attr, '__scrape_update__'):
                    attr(id_, timestamp, soup)
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error("Encountered error parsing %s: %s" % (id_, e))
                continue

        # Send the rest of message contents to redis
        self.redis.sadd('daftpunk:properties', id_)
        self.redis.rpush('daftpunk:%s:timestamps' % id_, timestamp)
        self.redis.set('daftpunk:%s:url' % id_, url)
        self.redis.set('daftpunk:%s:html' % id_, html)
        self.redis.set('daftpunk:%s:tag' % id_, tag)
        self.redis.set('daftpunk:%s:category' % id_, category)

        return id_

    @scrape_update
    def pricing(self, id_, timestamp, soup):
        price = soup.find(id="smi-price-string")
        if price:
            currency = price.string[0]
            value = price.string[1:].replace(',', '.')

            self.redis.zadd('daftpunk:%s:price' % id_, value, timestamp)
            self.redis.set('daftpunk:%s:currency' % id_, currency)

    @scrape_once
    def ber_rating(self, id_, timestamp, soup):
        ber = soup.find(**{'class':"ber-icon"})
        ber_number = ber['id'] if ber else ''
        ber_rating = BER_RATINGS.index(ber_number)

        self.redis.set('daftpunk:%s:ber' % id_, ber_rating)

    @scrape_once
    def phone_numbers(self, id_, timestamp, soup):
        phones = set()
        phone_class = soup.find(**{'class':"phone1"})
        if phone_class:
            phone_strs = phone_class.text.split()
            phone_strs = [re_sub('[+()]', '', z) for z in phone_strs]
            for i in reversed(range(len(phone_strs))):
                if not phone_strs[i].isdigit():
                    phones.add('-'.join(phone_strs[i+1:]))
                    phone_strs = phone_strs[:i]

        self.redis.sadd('daftpunk:%s:phone_numbers' % id_, *phones)

    @scrape_once
    def address(self, id_, timestamp, soup):
        address = soup.find(id="address_box").h1.text

        self.redis.set('daftpunk:%s:address' % id_, address)

    @scrape_once
    def geocode(self, id_, timestamp, soup):
        if not self.is_geocoded(id_):
            address = self.redis.get('daftpunk:%s:address' % id_)
            payload = {'address': address}
            req = req_get(GEOCODE_API, params=payload)
            results = req.json()['results']

            # Not sure how often google returns multiple results
            if len(results) > 1:
                with open('./daft.%s.log' % self.prop_id, 'a') as outp:
                    json_dump(results, outp)

            lat_long = results[0]['geometry']['location']
            self.redis.set('daftpunk:%s:lat' % id_, lat_long['lat'])
            self.redis.set('daftpunk:%s:long' % id_, lat_long['lng'])

    def is_geocoded(self, id_):
        lat = self.redis.get('daftpunk:%s:lat' % id_)
        long_ = self.redis.get('daftpunk:%s:long' % id_)
        return (lat and long_)

    @scrape_once
    def description_and_tokens(self, id_, timestamp, soup):
        overview = soup.find(id="description")
        for scr in overview.find_all('script'):
            scr.clear()

        desc = overview.text
        tokens = word_tokenize(desc)
        freqdist = FreqDist(tokens)

        self.redis.set('daftpunk:%s:description' % id_, desc)
        for token, freq in freqdist.iteritems():
            self.redis.zadd('daftpunk:%s:tokens' % id_, freq, token)

    @scrape_once
    def photos(self, id_, timestamp, soup):
        carousel = soup.find(id='pbxl_carousel')
        for img in carousel.find_all('img'):
            url = 'http:' + img.attrs['data-original']

            self.redis.rpush('daftpunk:%s:image_urls' % id_, url)
            resp = req_get(url, stream=True)
            if resp.status_code == 200:
                self.redis.rpush('daftpunk:%s:images' % id_, resp.raw.read())

    @staticmethod
    def strip_url(url):
        split_results = urlsplit(url)
        path = split_results.path

        path_match = re_match("/(sales|lettings)/(.*?)/(\d*)/?", path)
        category, tag, prop_id = path_match.groups() \
                if path_match \
                else ("", "", "")

        return category, tag, prop_id

    def process_message(self, body):
        prop = {}
        message = json_loads(body)
        url, timestamp, html = message

        id_ = self.scrape_all(url, timestamp, html)

        return id_

if __name__ == "__main__":
    x = DpWorker({})
