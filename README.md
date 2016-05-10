# Climate Change API

## Development Environment

To get started, run these commands inside the `api` directory:

```bash
vagrant up
vagrant ssh
cd climate-change-api
docker-compose up
```

The Django app will be exposed on port 8080.

### Django Management commands

To run Django management commands, use the console helper script:

```bash
cd /vagrant
./scripts/console django './manage.py migrate'
```
