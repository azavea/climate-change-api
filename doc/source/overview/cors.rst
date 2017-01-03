Cross-Origin Resource Sharing (`CORS`__)
'''''''''''''''''''''''''''''''''''''

__ https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS

As this API is designed for public use, it supports HTTP requests from any origin. To demonstrate, a sample request from an outside domain::

   curl -i https://staging.api.futurefeelslike.com/api/scenario -H "Origin:https://azavea.com" -X OPTIONS
   
   HTTP/1.1 301 Moved Permanently
   Access-Control-Allow-Headers: x-requested-with, content-type, accept, origin, authorization, x-csrftoken, user-agent, accept-encoding
   Access-Control-Allow-Methods: GET, PUT, PATCH, DELETE, POST, OPTIONS
   Access-Control-Allow-Origin: *
   Access-Control-Max-Age: 86400
   Content-Type: text/html; charset=utf-8
   Date: Tue, 03 Jan 2017 20:32:02 GMT
   Location: /api/scenario/
   Server: gunicorn/19.4.5    
   X-Frame-Options: SAMEORIGIN    
   Content-Length: 0
   Connection: keep-alive
