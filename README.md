# daftpunk

Scrapes details from daft.ie and stores it in Redis.

## Installation

### On ubuntu

First install rabbitmq and enable the admin web console:

```
sudo apt-get install rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management
sudo service rabbitmq-server restart
```

Next up, install redis:
```
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
sudo make install
```

Then install python plugins:
```
sudo pip install pika requests beautifulsoup4 redis
```

## Proposed redis schema

* properties -> z(prop_id, ...)
* properties:sales -> z(prop_id, ...)
* properties:lettings -> z(prop_id, ...)

* prop_id:url -> string
* prop_id:host -> string
* prop_id:path -> string
* prop_id:category -> string
* prop_id:tag -> string
