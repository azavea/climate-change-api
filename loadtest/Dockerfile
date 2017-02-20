FROM python:2.7

MAINTAINER Azavea

RUN apt-get update && apt-get install -y --no-install-recommends \
    python-dev \
    ipython \
    python-pip \
    python-matplotlib \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    tcl-dev tk-dev python-tk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./ /opt/loadtest

WORKDIR /opt/loadtest

ENTRYPOINT ["/bin/bash"]
