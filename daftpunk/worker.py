from pika import BlockingConnection, ConnectionParameters
from json import loads as json_loads
from redis import StrictRedis
from functools import partial
from daftpunk import GEOCODE_API, PROPERTIES, BER_RATINGS
from bs4 import BeautifulSoup

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

class DpParser(object):
    def __init__(self, config):
        self.config = config
        self.redis = StrictRedis(host='localhost', port=6379, db=0)

    def process_message(self, body):
        prop = {}
        message = json_loads(body)
        id_, timestamp, html = message

        # Send message contents to redis
        self.redis.sadd('daftpunk:properties', id_)
        self.redis.rpush('daftpunk:%s:timestamps' % id_, timestamp)
        self.redis.set('daftpunk:%s:html' % id_, html)

        # parse relevant information from html
        soup = BeautifulSoup(html)

        # Pricing
        price = soup.find(id="smi-price-string").string
        self.redis.zadd('daftpunk:%s:price' % id_, timestamp, price)

        # BER Rating
        ber = soup.find(**{'class':"ber-icon"})
        ber_number = ber['id'] if ber else ''
        ber_rating = BER_RATINGS.index(ber_number)
        self.redis.set('daftpunk:%s:ber' % id_, ber_rating)

        # Phone Numbers
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

        # Address
        address = soup.find(id="address_box").h1.text
        self.redis.set('daftpunk:%s:address' % id_, address)

        # Geocoding
        self.run_geocode(id_)

        return id_

    def is_geocoded(self, id_):
        lat = self.redis.get('daftpunk:%s:lat' % id_)
        long_ = self.redis.get('daftpunk:%s:long' % id_)
        return (lat and long_)

    def run_geocode(self, id_):
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
            self.redis.set('daftpunk:%s:long' % id_, lat_long['long'])

if __name__ == "__main__":
    x = DpWorker({})
