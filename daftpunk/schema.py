from lament import *

class DpConfig(LamentConfig):
    @config(list)
    def queries(self, config, obj):
        config.extend(obj)
        return config
