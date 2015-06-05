from lament import *

class DpConfig(object):
    @config(dict)
    def queries(self, config, obj):
        config.extend(obj)
        return config
