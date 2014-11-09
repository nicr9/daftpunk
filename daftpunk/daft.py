from requests import get as req_get
from bs4 import BeautifulSoup
from urlparse import urlsplit
from re import match
from re import sub as re_sub
from json import dump as json_dump
from daftpunk import GEOCODE_API, PROPERTIES, BER_RATINGS

class DaftProperty(object):
    def __init__(self, prop_id, data):
        self.prop_id = prop_id
        self.data = data

    @classmethod
    def from_url(cls, url):
        split_results = urlsplit(url)

        path = split_results.path
        category, tag, prop_id = cls.strip_from_path(path)

        data = {
                'url': url,
                'host': split_results.netloc,
                'path': path,
                'category': category,
                'tag': tag,
                }

        if prop_id:
            temp = cls(prop_id, data)
            temp.scrape()

            return temp

    @classmethod
    def from_redis(cls, r, prop_id):
        keys = r.keys("%s:*" % prop_id)

        data = {}
        for r_key in keys:
            type_ = r.type(r_key)
            key = r_key.split(':')[-1]
            if type_ == "string":
                data[key] = r.get(r_key)
            elif type_ == "list":
                data[key] = r.lrange(r_key, 0, -1)
            elif type_ == "set":
                data[key] = r.smembers(r_key)

        temp = cls(prop_id, data)
        return temp

    def is_geocoded(self):
        geocoded = 'lat' in self.data and 'long' in self.data
        return geocoded

    def run_geocode(self, verbose=False):
        if not self.is_geocoded():
            payload = {'address': self.data['address']}
            if verbose:
                print "Geocoding:", self.data['address']
            req = req_get(GEOCODE_API, params=payload)
            results = req.json()['results']

            # Not sure how often google returns multiple results
            if len(results) > 1:
                with open('./daft.%s.log' % self.prop_id, 'a') as outp:
                    json_dump(results, outp)

            lat_long = results[0]['geometry']['location']
            self.data.update(lat_long)

    @staticmethod
    def strip_from_path(path):
        path_match = match("/(sales|lettings)/(.*?)/(\d*)/?", path)
        
        category, tag, prop_id = path_match.groups() \
                if path_match \
                else ("", "", "")

        return category, tag, prop_id

    def scrape(self):
        req = req_get(self.data['url'])
        soup = BeautifulSoup(req.text)

        # Pricing
        price = soup.find(id="smi-price-string").string

        # BER Rating
        ber = soup.find(**{'class':"ber-icon"})
        ber_rating = ber['id'] if ber else ''
        ber_score = BER_RATINGS.index(ber_rating)

        # Phone Numbers
        phone_strs = soup.find(**{'class':"phone1"}).text.split()
        phone_strs = [re_sub('[+()]', '', z) for z in phone_strs]
        phones = set()
        for i in reversed(range(len(phone_strs))):
            if not phone_strs[i].isdigit():
                phones.add('-'.join(phone_strs[i+1:]))
                phone_strs = phone_strs[:i]

        # Address
        address = soup.find(id="address_box").h1.text

        data = {
                'price': price[1:],
                'currency': price[0],
                'ber_rating': ber_rating,
                'ber_score': ber_score,
                'phone': phones,
                'address': address,
                }
        self.data.update(data)

        self.run_geocode()

    def export(self, r):
        r.sadd(PROPERTIES, self.prop_id)
        r.sadd(
                "%s:%s" % (PROPERTIES, self.data['category']),
                self.prop_id
                )

        for key, val in self.data.iteritems():
            if isinstance(val, basestring):
                r.set(
                        "%s:%s" % (self.prop_id, key),
                        val
                        )
            elif isinstance(val, set):
                for elem in val:
                    r.sadd(
                            "%s:%s" % (self.prop_id, key),
                            elem
                            )
            elif isinstance(val, list):
                for elem in val:
                    r.rpush(
                            "%s:%s" % (self.prop_id, key),
                            elem
                            )
            else:
                print "Had trouble exporting %s:%s:%s" % (prop_id, key, val)
