FROM quay.io/azavea/django:1.9.6

MAINTAINER Azavea

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev \
    libmemcached-dev python-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip install --upgrade pip && pip install numpy && pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./ /opt/django

WORKDIR /opt/django/climate_change_api

EXPOSE 8080

CMD ["-w", "2", \
     "-b", "0.0.0.0:8080", \
     "--reload", \
     "--log-level", "info", \
     "--error-logfile", "-", \
     "--forwarded-allow-ips", "*", \
     "-k", "gevent", \
     "climate_change_api.wsgi"]
