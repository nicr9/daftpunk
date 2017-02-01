import re


class DaftResource(object):
    def __init__(self, redis):
        self.redis = redis

    @classmethod
    def get_all(cls, redis):
        codes = redis.hkeys("dp:{}".format(cls._type))
        return [cls.from_code(redis, code) for code in codes]

    @classmethod
    def from_code(cls, redis, code):
        self = cls(redis)
        self.code = code
        return self

    def key(self, attr=None):
        if attr:
            return "dp:{}:{}:{}".format(self._type, self.code, attr)

        return "dp:{}:{}".format(self._type, self.code)

    @property
    def label(self):
        return self.redis.hget(
                "dp:{}".format(self._type), self.code).decode('utf-8')

class County(DaftResource):
    _type = 'counties'

    @property
    def areas(self):
        areas = self.redis.lrange(self.key(), 0 ,-1)
        return [Area.from_code(self.redis, z) for z in areas]

class Area(DaftResource):
    _type = 'areas'

class RegionStats(DaftResource):
    _type = 'regionstats'

    @property
    def url(self):
        return self.redis.get(self.key('url'))

    @url.setter
    def url(self, value):
        self.redis.set(self.key('url'), value)

    @property
    def current(self):
        return [Property.from_code(self.redis, code)
                for code in self.redis.lrange(self.key('current'), 0, -1)]

    @current.setter
    def current(self, value):
        key = self.key('current')
        self.redis.delete(key)
        self.redis.lpush(key, *value)

    @property
    def count(self):
        return self.redis.llen(self.key('current'))

class Property(DaftResource):
    _type = 'properties'

    @property
    def url(self):
        return self.redis.get(self.key('url'))

    @url.setter
    def url(self, value):
        self.redis.set(self.key('url'), value)

    @property
    def address(self):
        return self.label.decode('utf-8')

    @address.setter
    def address(self, value):
        self.redis.hset("dp:{}".format(self._type), self.code, value)

    def set_price(self, raw):
        match = re.search(
                r"^([\u20ac\u00a3\u0024])?([\d,.]*)(.*)?$", raw)

        if match.group(0):
            self.redis.set(self.key('price_string'), match.group(0))
        if match.group(1):
            self.redis.set(self.key('currency'), match.group(1))
        if match.group(2):
            self.redis.set(self.key('price'), match.group(2).replace(',', ''))
        if match.group(3):
            self.redis.set(self.key('pricing'), match.group(3))

    @property
    def price_string(self):
        return self.redis.get(self.key('price_string')).decode('utf-8')

    @property
    def currency(self):
        return self.redis.get(self.key('currency')).decode('utf-8')

    @property
    def price(self):
        return int(self.redis.get(self.key('price')))

    @property
    def pricing(self):
        return self.redis.get(self.key('pricing'))

    @property
    def ber(self):
        return self.redis.get(self.key('ber'))

    @ber.setter
    def ber(self, value):
        self.redis.set(self.key('ber'), value)

class Question(DaftResource):
    _type = 'questions'

    @property
    def score(self):
        return int(self.redis.get(self.key('score')))

    @property
    def active(self):
        return self.redis.exists(self.key('active'))

    @active.setter
    def active(self, value):
        if value:
            self.redis.set(self.key('active'), '')
        else:
            self.redis.delete(self.key('active'))
