### Base Dockerfile to support the Vapor package ###
FROM python:3.12-slim

WORKDIR /vapor 

# See .dockerignore for which files are excluded
COPY . .

# Install the package
RUN pip install -e .

ENV VAPOR_DATA_PATH="/vapor/data"
