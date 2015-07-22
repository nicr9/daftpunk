# daftpunk

Scrapes details from daft.ie and stores it in Redis.

## Installation

### Using docker

For help getting docker and docker-compose installed [checkout this page.](https://docs.docker.com/compose/install/)

First install the daftpunk CLI tool:

```
sudo python setup.cli install
```

Then to build all the services and start them run the following:

```
sudo daftpunk go
```

This will start up the message queue, database, worker and a web frontend container.

The worker will perform a search every day at midnight and process any resulting property pages.

If you're developing and would like to trigger a search at will, run the following:

```
sudo daftpunk search
```

At this point you can direct your browser to `localhost:5000` to see the frontend.

**N.B.** If you're using docker-machine to host these containers remotely, you'll need to replace `localhost` with the IP of the docker-engine. You can find the engine IP by running `docker-machine ip <machine-name>`

### Manually on ubuntu

**WARNING: Not officially supported, proceed with caution.**

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
sudo python2.7 setup.docker install
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

Finally start the frontend server:

```
cd frontend
python server.py
```

This will be served on `localhost:5000`.

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
