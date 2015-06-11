FROM ubuntu:14.04
MAINTAINER Nic Roland "nicroland9@gmail.com"

RUN apt-get update
RUN apt-get install -y python python-pip
RUN pip install flask redis

ADD . /opt/frontend
WORKDIR /opt/frontend

EXPOSE 5000

ENTRYPOINT python ./server.py
