from pika import BlockingConnection, ConnectionParameters
from json import loads as json_loads

RABBIT_QUEUE = 'daftpunk'

class DpWorker(object):
    def __init__(self, config):
        self.config = config
        self.run()

    def open_channel(self):
        conn = BlockingConnection(ConnectionParameters('localhost'))
        channel = conn.channel()
        channel.queue_declare(queue=RABBIT_QUEUE)

        return channel

    def process_message(self, body):
        prop = {}
        message = json_loads(body)
        prop['id'], prop['html'] = message

        return prop

    def run(self):
        channel = self.open_channel()

        def callback(ch, method, properties, body):
            prop = self.process_message(body)
            print " [x] Received %r" % (prop['id'],)

        channel.basic_consume(
                callback,
                queue=RABBIT_QUEUE,
                no_ack=True
                )

        print ' [*] Waiting for messages. To exit press CTRL+C'
        channel.start_consuming()

if __name__ == "__main__":
    x = DpWorker({})
