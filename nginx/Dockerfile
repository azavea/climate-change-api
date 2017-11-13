FROM nginx:1.12

RUN mkdir -p /etc/nginx/includes
RUN mkdir /srv/dist
RUN chown nginx:nginx -R /srv/dist/

COPY etc/nginx/nginx.conf /etc/nginx/nginx.conf
COPY etc/nginx/includes/*.conf /etc/nginx/includes/
COPY etc/nginx/conf.d/app/*.conf /etc/nginx/conf.d/
