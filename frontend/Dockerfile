FROM ubuntu:14.04
MAINTAINER Nic Roland "nicroland9@gmail.com"

RUN apt-get update
RUN apt-get install -y python python-pip
RUN pip install flask redis

ADD . /opt/frontend

EXPOSE 5000

WORKDIR /opt/frontend
ENTRYPOINT python ./server.py
