# daftpunk

Scrapes details from daft.ie and stores it in Redis.

## Installation

### Using docker

For help getting docker and docker-compose running [checkout this page.](https://docs.docker.com/compose/install/)

Then to build all the services and start them run the following:

```
sudo docker-compose build
sudo docker-compose up
```

This will start up the message queue, database and a worker container.

Then to perform a search and process any property pages run:

```
sudo docker exec -d daftpunk_worker_1 dp_worker
sudo docker exec -it daftpunk_worker_1 dp_searcher
```

At this point you can direct your browser to `localhost:5000` to see the frontend.

### Manually on ubuntu

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

Then install all the python bits:
```
sudo pip install pika requests beautifulsoup4 redis nltk
sudo python2.7 setup.py install
python2.7 -c "import nltk; nltk.download('punkt')"
```

Final step is to create a config file:

```
sudo mkdir /etc/daftpunk/
sudo cp daftpunk/config/localhost.json /etc/daftpunk/config.json
```

Then to perform a search and process any property pages run:

```
dp_searcher
dp_worker
```

## Redis schema

* daftpunk:properties -> {<prop_id>, ...}
* daftpunk:<prop_id>:timestamps -> [<timestamp>, ...]
* daftpunk:<prop_id>:html -> string
* daftpunk:<prop_id>:category -> string

* daftpunk:<prop_id>:price -> z{<timestamp>:string, ...}
* daftpunk:<prop_id>:currency -> string
* daftpunk:<prop_id>:current_price -> string
* daftpunk:<prop_id>:ber -> string
* daftpunk:<prop_id>:phone_numbers -> {string}
* daftpunk:<prop_id>:address -> string
* daftpunk:<prop_id>:lat -> string
* daftpunk:<prop_id>:long -> long
* daftpunk:<prop_id>:description -> string
* daftpunk:<prop_id>:tokens -> z{string: float, ...}
* daftpunk:<prop_id>:image_urls -> [url, ...]
* daftpunk:<prop_id>:images -> [binary, ...]
