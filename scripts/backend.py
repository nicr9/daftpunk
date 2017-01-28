import os
from urlparse import urlparse

import psycopg2
from redis import StrictRedis
from dp2.client import DaftClient


class DaftSearcher(object):
    def __init__(self):
        """
        Connect to pgsql and redis, initiate search
        """
        pg_url = urlparse(os.environ['DATABASE_URL'])
        self.pgsql = psycopg2.connect(
                database=pg_url.path[1:],
                user=pg_url.username,
                password=pg_url.password,
                host=pg_url.hostname)

        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis = StrictRedis.from_url(redis_url)

        self.client = DaftClient(self.redis)

        self.run()

    @property
    def regions(self):
        with self.pgsql.cursor() as cur:
            cur.execute("SELECT county, area, property_type, sha from region")
            return cur.fetchall()

    def run(self):
        for query in self.regions:
            for property_code in self.client.search(*query[:-1]):
                self.client.update_property(property_code)
            with self.pgsql.cursor() as cur:
                cur.execute("UPDATE region SET last_scraped = NOW() WHERE sha = '{}'".format(query[-1]))
                self.pgsql.commit()

if __name__ == "__main__":
    DaftSearcher()
