FROM node:12-alpine

RUN \
    addgroup -S statsd \
    && adduser -D -S -h /var/lib/statsd -s /sbin/nologin -G statsd statsd \
    && apk add --no-cache --virtual .build-deps \
    ca-certificates \
    g++ \
    make \
    python \
    tar \
    wget \
    && wget -qO- https://github.com/etsy/statsd/archive/v0.8.2.tar.gz \
    | tar --strip-components=1 -xzC /var/lib/statsd \
    && (cd /var/lib/statsd && yarn add statsd-librato-backend@2.0.13) \
    && apk del .build-deps

USER statsd
WORKDIR /var/lib/statsd
COPY var/lib/statsd/config.js /var/lib/statsd/config.js

ENTRYPOINT ["node", "stats.js"]
CMD ["config.js"]
