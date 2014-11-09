REDIS_CONFIG = {
        'host': 'localhost',
        'port': 6379,
        'db': 0
        }
GEOCODE_API = "https://maps.googleapis.com/maps/api/geocode/json"
PROPERTIES = "properties"
BER_RATINGS = [
        '', # Unknown
        'ber-G',
        'ber-F',
        'ber-E2',
        'ber-E1',
        'ber-D2',
        'ber-D1',
        'ber-C3',
        'ber-C2',
        'ber-C1',
        'ber-B3',
        'ber-B2',
        'ber-B1',
        'ber-A3',
        'ber-A2',
        'ber-A1',
        ]

class DaftMeta(type):
    def __new__(mcls, name, bases, cdict):
        handlers = {}

        ignored = set(['__module__', '__metaclass__', '__doc__'])
        for key, value in cdict.items():
            if key not in ignored:
                if hasattr(value, '__daftpunk__'):
                    handlers[key] = value

        cdict['COMMANDS'] = handlers

        return super(DaftMeta, mcls).__new__(mcls, name, bases, cdict)

def daftcommand(func):
    setattr(func, '__daftpunk__', None)
    return func
