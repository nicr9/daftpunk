#! /usr/bin/env python2.7
import sys
from pprint import pprint

from dp2.client import DaftClient

class DP2(object):
    def __init__(self, username, password):
        self.client = DaftClient(username, password)

if __name__ == "__main__":
    dp = DP2(*sys.argv[1:3])
    pprint(dp.client.get_regions('Co. Kildare'))
