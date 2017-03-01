import json

import dredd_hooks as hooks


stash = {}
email = 'testuser@testing.com'
password = 'thisisatest'


@hooks.before('/api-token-auth/ > POST > 200 > application/json')
def get_token(transaction):
    # retrieve token from test user
    transaction['request']['body'] = 'email=' + email + '&password=' + password


@hooks.after('/api-token-auth/ > POST > 200 > application/json')
def stash_token(transaction):
    # hook to retrieve token from test user account
    parsed_body = json.loads(transaction['real']['body'])
    stash['token'] = parsed_body['token']


@hooks.before_each
def add_token_to_requests(transaction):
    # append token to each API request
    if transaction['name'] == '/api-token-auth/ > POST > 200 > application/json':
        return
    elif stash['token']:
        transaction['request']['headers']['Authorization'] = 'Token ' + stash['token']
