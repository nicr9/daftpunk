from pykml.factory import KML_ElementMaker as KML

class DpProperty(object):
    def __init__(self, id_):
        self.id_ = id_
        self.redis = StrictRedis(host='localhost', port=6379, db=0)

    def kml_placemark(self):
        return KML.Placemark(
                KML.name(self.redis.get('daftpunk:%s:address')),
                KML.Point(
                    KML.coordinates(
                        ','.join([
                            self.redis.get('daftpunk:%s:long' % self.id_),
                            self.redis.get('daftpunk:%s:lat' % self.id_)
                            ])
                        )
                    ),
                KML.description(self.redis.get('daftpunk:%s:description' % self.id_)),
                )
