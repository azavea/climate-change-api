## Using Librato in development

#### Create an API token

Log in to the climate Librato account. If you haven't been invited, request an invite from Hector or Andrew on Slack.

Go to Account Settings -> API Tokens -> Generate New API Token.

Create a 'Record Only' token and name it something like 'Development -- <your name>'

#### Setting up dev environment to push to Librato instead of console

First, copy the example librato statsite config:
```
cp statsite/etc/statsite/librato.ini.example statsite/etc/statsite/librato.ini
```

Then add the Librato account email and token to the newly created `librato.ini` file.

If you've already setup your VM, then you can rebuild your containers with `docker-compose build`, otherwise, continue with VM setup in the project README.

**NOTE:** This README contains temporary instructions that should be removed along with `./statsite` when #488 is addressed. Ensure the instructions that reference this document in the project README are also removed.
