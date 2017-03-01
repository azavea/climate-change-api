FROM node:6.3.1

MAINTAINER Azavea

RUN apt-get update && apt-get install -y \
    python-pip

RUN npm install -g dredd@2.2.3

RUN pip install --upgrade pip && pip install "dredd-hooks~=0.1.2"
