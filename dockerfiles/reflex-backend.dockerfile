FROM python:3.12-slim

ARG REFLEX_REDIS_URL
ENV REDIS_URL=${REFLEX_REDIS_URL}
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY ./reflex-ui .

RUN pip install -r requirements.txt


ENTRYPOINT ["reflex", "run", "--env", "prod", "--backend-only", "--loglevel", "debug" ]