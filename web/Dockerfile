FROM nicr9/dp2-base
MAINTAINER Nic Roland "nicroland9@gmail.com"

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENTRYPOINT python /usr/src/app/app.py
