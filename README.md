# daftpunk

Scrapes details from daft.ie and stores it in Redis.

## Installation

### Install/Run on Docker

For help getting docker and docker-compose installed [checkout this page.](https://docs.docker.com/compose/install/)

You'll also need [python2.7](https://www.python.org/downloads/release/python-279/) and the [setuptools package](https://pypi.python.org/pypi/setuptools)!

Next, you'll want to install the daftpunk CLI tool:

```
sudo python setup.cli install
```

Then to build all the services and start them run the following:

```
sudo daftpunk go
```

This starts up the message queue, database, worker and a web frontend as containers.

The worker is set up to perform a search and process results every day at midnight.

If you're a developer and need to trigger a search at will, run the following:

```
sudo daftpunk search
```

At this point you can direct your browser to `localhost:5000` to see the frontend.

**N.B.**

If you're using docker-machine to host these containers remotely, you'll need to replace `localhost` with the IP of the docker-engine.
You can find the engine IP by running:

```
docker-machine ip <machine-name>
```

### Install Manually on Ubuntu

**WARNING: Not officially tested/maintained, proceed with caution.**

These instructions describe how to set up daftpunk without using docker. For this you won't need to install the daftpunk CLI tool (because it's purpose is mostly to simplify long docker commands.)

If you try this and find the instructions here to be inaccurate/insufficient, please open a pull request. You're help will be greatly appriciated (even if it's just correcting my awful typos!)

If, on the other hand, you try this and run into blocking issues, get in contact, we're happy to help!

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
dp_worker # This command will block indefinitely
```

Finally, in an other shell, start the frontend server:

```
cd frontend
python server.py
```

This will be served on `localhost:5000`.

## Author

Name: Nic Roland
Email: nicroland9@gmail.com
Twitter: @nicr9_

## Contributors

* [Peter Keogh](https://github.com/keoghpe)
* [Kingsley Kelly](https://github.com/KingsleyKelly)
