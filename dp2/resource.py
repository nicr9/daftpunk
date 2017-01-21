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
        return self.redis.hget("dp:{}".format(self._type), self.code)

class County(DaftResource):
    _type = 'counties'

    @property
    def regions(self):
        regions = self.redis.lrange(self.key(), 0 ,-1)
        return [Region.from_code(self.redis, z) for z in regions]

class Region(DaftResource):
    _type = 'regions'

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
        return self.label

    @address.setter
    def address(self, value):
        self.redis.hset("dp:{}".format(self._type), self.code, value)
