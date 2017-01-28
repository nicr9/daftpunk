import json
import os
import hashlib

from sys import argv

from redis import StrictRedis
from redis.exceptions import ResponseError

questions_key = "dp:questions"
score_key = "dp:questions:{}:score"
active_key = "dp:questions:{}:active"
all_data = "dp:questions*"

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis = StrictRedis.from_url(redis_url)

if argv[1] == "update":
    with open("./data/questions.json", 'r') as inp:
        data = json.load(inp)

    labels = {}
    for text, score, active in data:
        md5 = hashlib.md5(text).hexdigest()
        labels[md5] = text

        redis.set(score_key.format(md5), score)
        if active:
            redis.set(active_key.format(md5), '')
        else:
            redis.delete(active_key.format(md5))

    redis.hmset(questions_key, labels)

elif argv[1] == "flush":
    try:
        redis.delete(*redis.keys(all_data))
    except ResponseError:
        pass
