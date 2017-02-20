FROM python:2.7

MAINTAINER Azavea

RUN apt-get update && apt-get install -y --no-install-recommends \
    ipython \
    python-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./ /opt/loadtest

WORKDIR /opt/loadtest

EXPOSE 8089

ENTRYPOINT ["/bin/bash"]

CMD ["-c", "locust --host=${API_HOST}"]
