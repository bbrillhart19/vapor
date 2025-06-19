### Base Dockerfile to support the Vapor package ###
FROM python:3.12-slim

WORKDIR /vapor 

# See .dockerignore for which files are excluded
COPY . .

RUN pip install -e .
