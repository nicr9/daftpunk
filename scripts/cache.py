import json
import os

from sys import argv

from dp2.client import DaftClient
from redis import StrictRedis

counties_key = "dp:counties"
all_counties = "dp:counties:*"
counties_template = "dp:counties:{}"
areas_key = "dp:areas"

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis = StrictRedis.from_url(redis_url)

if argv[1] == "retrieve":
    client = DaftClient(redis)
    for county in client.update_counties():
        client.update_areas(county)

elif argv[1] == "backup":
    data = {}

    data[counties_key] = redis.hgetall(counties_key)
    data[areas_key] = redis.hgetall(areas_key)

    for code in data[counties_key]:
        key = counties_template.format(code)
        data[key] = redis.lrange(key, 0, -1)

    with open("./data/cache.json", 'w') as outp:
        json.dump(data, outp)

elif argv[1] == "flush":
    try:
        redis.delete(counties_key)
    except ResponseError:
        pass

    try:
        redis.delete(*redis.keys(all_counties))
    except ResponseError:
        pass

    try:
        redis.delete(areas_key)
    except ResponseError:
        pass


elif argv[1] == "restore":
    with open("./data/cache.json", 'r') as inp:
        data = json.load(inp)

    redis.hmset(counties_key, data.pop(counties_key))
    redis.hmset(areas_key, data.pop(areas_key))

    # Remaining keys should be just dp:counties:*
    for key in data:
        redis.lpush(key, *data[key])
