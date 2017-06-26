FROM quay.io/azavea/statsite:0.8-alpine

MAINTAINER Azavea <systems@azavea.com>

COPY etc/statsite/statsite.cfg /etc/statsite/statsite.cfg

COPY etc/statsite/librato.ini /etc/statsite/librato.ini

COPY usr/libexec/statsite/librato.py /usr/libexec/statsite/librato.py
