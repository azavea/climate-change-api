# Climate Change API

## Development Environment

To get started, run these commands:

```bash
vagrant up
vagrant ssh
cd climate-change-api
docker-compose up
```

The Django app will be exposed on port 8080.

All further commands assume you are first in the directory `~/climate-change-api` inside the vagrant vm.


### Documentation

Documentation for the API can be built with:
```bash
./scripts/docs
```
Then it can be served with:
```bash
cd doc/build/html && python -m SimpleHTTPServer 8088
```
and viewed at http://localhost:8088


### Django Management commands

To run Django management commands, use the console helper script:

```bash
./scripts/console django './manage.py migrate'
```
