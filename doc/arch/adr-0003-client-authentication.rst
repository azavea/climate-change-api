Climate Data Authentication
===========================

Context
-------

This project provides access to the data via a Django Rest Framework API in three different ways:

 - logging in to the DRF admininstrative web interface, using the built-in session authentication
 - directly querying the API with a provided token
 - logging in to the [Angular client web app](https://github.com/azavea/climate-change-lab)

Two options for the client application to authenticate with the API have been suggested:


**Session Authentication**

Redirect to DRF administrative interface for login and new account creation. Client application
would read Django CSRF token from its cookie and append it as a request header to API queries.

Advantages include potential re-use of login and signup pages and mitigation of potential for XSS
attacks by limiting access to the domain and sub-domains of the cookie.

Disadvantages include:

 - Development workflow of running web app locally against remote API will no longer work.
 - Client web app must be hosted on the same domain or sub-domain as the API, or modifications must
   be made to the built-in session authentication to also append the cookie to the appropriate
   domain.
 - Client app will become stateful, which will make scaling difficult; requests must be pinned to
   the server against which the app is authenticated, or session must be managed by an independent
   server (such as redis).
 - Administrative interface will require modification to redirect back to client web app after login
   or sign up (but still redirect to DRF administrative interface when not logging in from client
   app).
 - Pontential for XSRF attacks. Django's CSRF token should mitigate this.


**Token Authentication**

Client application appends user token as a request header to API queries.

Advantages include no potential for XSRF attacks; a stateless setup that will ease scaling; the
ability to run the client application on any domain, including under local development; and ease of
potential further uses of tokens, such as authenticating within a mobile application or from other
applications we may wish to build.

Disadvantages include:

 - Potential for XSS attacks. Sanitization of input by Angular should mitigate this; also, the
   nature of the web app is primarily read-only, apart from storing project settings data which does
   not come from direct user input.
 - New API endpoint will need to be created for obtaining a token from username/password login, and
   client app will need to use its own login page. Sign-up process could still potentially redirect
   to administrative interface on API, however. API endpoint for obtaining token can be written
   using previous DRF projects as an example.


Decision
--------

Token authentication provides greater flexibility for a small amount of initial setup work around
client app login, has potential for re-use in other applications against the API for which session
authentication may be impractical, and will ease scaling systems. As we already provide and should
continue to support user tokens and CORS to clients for them to access the API directly, the
potential for XSS or otherwise unauthorized use of the user tokens against the API already exists
and should be taken under consideration.


Consequences
------------

Care should be taken in authoring the client web app to properly sanitize input through Angular
controls before passing any POST or PATCH to the API. Further, regardless of the choice of client
app authentication, we should be careful to protect our data and consider what is available to
modify through API endpoints, and to whom, in order to mitigate the potential for token abuse.
