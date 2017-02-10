import dredd_hooks as hooks


email = 'null@null.com'  # placeholder
password = 'null'  # placeholder


@hooks.before_each
def special_handling_api_token_POST(transaction):
    if transaction['id'] == 'POST /api-token-auth/':
        #print transaction
        transaction['request']['body'] = 'email=' + email + '&password=' + password
