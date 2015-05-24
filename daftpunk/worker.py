from pika import BlockingConnection, ConnectionParameters
from json import loads as json_loads
from redis import StrictRedis
from functools import partial

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

        return id_

if __name__ == "__main__":
    x = DpWorker({})
