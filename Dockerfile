FROM ubuntu:14.04
MAINTAINER Nic Roland "nicroland9@gmail.com"

RUN apt-get install -y python python-setuptools

ADD . /opt/daftpunk
WORKDIR /opt/daftpunk
RUN python2.7 setup.py install

ADD daftpunk/config/docker.json /etc/daftpunk/config.json
