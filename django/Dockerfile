FROM quay.io/azavea/django:1.9-python2.7-slim

MAINTAINER Azavea

COPY requirements.txt /tmp/

RUN set -ex \
    && deps="\
        libgdal-dev \
        libmemcached-dev \
        python-dev \
        make \
    " \
    && buildDeps="\
        build-essential \
        git \
    "\
    && apt-get update && apt-get install -y ${buildDeps} ${deps} --no-install-recommends \
    && pip install --no-cache-dir \
           numpy==$(grep "numpy" /tmp/requirements.txt | cut -d= -f3) \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -rf /tmp/* \
    && apt-get purge -y --auto-remove ${buildDeps} \
    && rm -rf /var/lib/apt/lists/* \
    && pip install django-static-precompiler[libsass]

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
