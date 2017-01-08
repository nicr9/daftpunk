FROM python:2
MAINTAINER Nic Roland "nicroland9@gmail.com"

WORKDIR /opt
COPY setup.py setup.cfg /opt/
COPY dp2 /opt/dp2/
RUN python setup.py develop
