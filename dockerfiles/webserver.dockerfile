FROM python:3.12-slim AS builder

WORKDIR /app

ARG REFLEX_API_URL
ENV API_URL=${REFLEX_API_URL}

RUN apt-get update -y && apt-get install curl unzip -y

COPY ./reflex-ui .
RUN pip install -r requirements.txt
RUN reflex export --frontend-only --no-zip

FROM nginx

COPY --from=builder /app/.web/build/client /usr/share/nginx/html
# COPY ./reflex-ui/nginx.conf /etc/nginx/conf.d/default.conf