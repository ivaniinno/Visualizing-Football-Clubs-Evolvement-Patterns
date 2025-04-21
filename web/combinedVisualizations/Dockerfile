FROM nginx:alpine

COPY default.conf /etc/nginx/conf.d/default.conf

RUN mkdir -p /var/www/html

COPY index.html /var/www/html/
COPY styles.css /var/www/html/
COPY scriptScatter.js /var/www/html/
COPY scriptMap.js /var/www/html/
COPY data/ /var/www/html/data/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]