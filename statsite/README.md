## Using Librato in development

#### Create an API token

Log in to climate Librato account.

Go to Account Settings -> API Tokens -> Generate New API Token.

Create a 'Record Only' token and name it something like 'Development -- <your name>'

#### Setting up dev environment to push to Librato instead of console

First, copy the example librato statsite config:
```
cp statsite/etc/statsite/librato.ini.example statsite/etc/statsite/librato.ini
```

Then add the Librato account email and token to the newly created `librato.ini` file.

Next, update docker-compose.yml with the following:
```
-   statsite:
-     image: quay.io/azavea/statsite:0.8-alpine
+   statsite:
+     build:
+       context: ./statsite
+       dockerfile: Dockerfile
```

Then run `docker-compose build && ./scripts/server` to run the dev server with Librato configured.

If all goes well, you should be able to hit the API and see metrics populate in the Librato account
within a minute or two.

To revert to statsite logging to console, simply revert the changes to `docker-compose.yml`.

**NOTE:** This README contains temporary instructions that should be removed along with `./statsite` when #488 is addressed.
