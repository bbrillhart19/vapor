FROM nginx

COPY --from=vapor-reflex /app/.web/build/client /usr/share/nginx/html
COPY ./reflex-ui/nginx.conf /etc/nginx/conf.d/default.conf