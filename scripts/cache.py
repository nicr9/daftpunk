import os
import json

from sys import argv
from redis import StrictRedis
from dp2.client import DaftClient

counties_key = "dp:counties"
all_counties = "dp:counties:*"
counties_template = "dp:counties:{}"
regions_key = "dp:regions"

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis = StrictRedis.from_url(redis_url)

if argv[1] == "retrieve":
    client = DaftClient(redis)
    for county in client.counties:
        client.get_region_codes(county)

elif argv[1] == "backup":
    data = {}

    data[counties_key] = redis.hgetall(counties_key)
    data[regions_key] = redis.hgetall(regions_key)

    for code in data[counties_key]:
        key = counties_template.format(code)
        data[key] = redis.lrange(key, 0, -1)

    with open("./data/cache.json", 'w') as outp:
        json.dump(data, outp)

elif argv[1] == "flush":
    redis.delete(counties_key)
    redis.delete(*redis.keys(all_counties))
    redis.delete(regions_key)

elif argv[1] == "restore":
    with open("./data/cache.json", 'r') as inp:
        data = json.load(inp)

    redis.hmset(counties_key, data.pop(counties_key))
    redis.hmset(regions_key, data.pop(regions_key))

    # Remaining keys should be just dp:counties:*
    for key in data:
        redis.lpush(key, *data[key])
