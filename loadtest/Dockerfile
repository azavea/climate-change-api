FROM python:2.7-slim

MAINTAINER Azavea

RUN apt-get update && apt-get install -y --no-install-recommends \
    python-dev \
    ipython \
    python-pip \
    python-matplotlib \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./ /opt/loadtest

WORKDIR /opt/loadtest

ENTRYPOINT ["/bin/bash"]

CMD ["multimech-run", "climate"]
