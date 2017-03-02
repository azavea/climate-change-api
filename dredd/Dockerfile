FROM node:6.3.1

MAINTAINER Azavea

COPY requirements.txt /tmp/

RUN \
    apt-get update \
    && apt-get install -y python-pip \
    && npm install -g dredd@2.2.3 \
    && pip install --upgrade pip && pip install -r /tmp/requirements.txt

# prevent node from running continuously
ENTRYPOINT [ "/usr/local/bin/dredd" ]
CMD [ "--version" ]
