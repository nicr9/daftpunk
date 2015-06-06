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
sudo pip install pika requests beautifulsoup4 redis nltk
```

To initialise nltk run `python -c "import nltk; nltk.download()"`, switch to models tab and download `punkt`.

Run this:
```
python setup.py install
```

## Proposed redis schema

* daftpunk:properties -> {<prop_id>, ...}
* daftpunk:<prop_id>:timestamps -> [<timestamp>, ...]
* daftpunk:<prop_id>:html -> string

* daftpunk:<prop_id>:price -> z{<timestamp>:string, ...}
* daftpunk:<prop_id>:currency -> string
* daftpunk:<prop_id>:ber -> string
* daftpunk:<prop_id>:phone_numbers -> {string}
* daftpunk:<prop_id>:address -> string
* daftpunk:<prop_id>:lat -> string
* daftpunk:<prop_id>:long -> long
* daftpunk:<prop_id>:description -> string
* daftpunk:<prop_id>:tokens -> z{string: float, ...}
* daftpunk:<prop_id>:images -> [binary, ...]
