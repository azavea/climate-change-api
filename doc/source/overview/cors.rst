Cross-Origin Resource Sharing (`CORS`__)
'''''''''''''''''''''''''''''''''''''

__ https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS

As this API is designed for public use, it supports HTTP requests from any origin. To demonstrate, a sample request from an outside domain::

   curl -i https://staging.api.futurefeelslike.com/api/scenario/ -H "Authorization: Token <your_api_token>" "Origin:https://azavea.com" -X OPTIONS

   HTTP/1.1 200 OK
   Allow: GET, HEAD, OPTIONS
   Content-Type: application/json
   Date: Thu, 05 Jan 2017 18:45:37 GMT
   Server: gunicorn/19.4.5
   Vary: Accept
   X-Frame-Options: SAMEORIGIN
   Content-Length: 398
   Connection: keep-alive
