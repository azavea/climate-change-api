## Climate API Statsd Container

### Testing metrics push to Librato

By default, the development statsd container only writes metrics to stdout, printed via docker logs.

If you'd like to re-configure your development environment to push to a Librato account, you'll need to:
```
cp statsd/var/lib/statsd/config.librato.js.example statsd/var/lib/statsd/config.js
```
Then, replace the values of `email` and `token` in `config.js` with the appropriate values from your Librato account.

Lastly, rebuild the statsd container with `docker-compose build statsd` and then restart your development services with `./scripts/server`. You should see metrics begin to populate in Librato.

**Note:** Ensure you do not commit any changes to `config.js` that contain Librato credentials.
