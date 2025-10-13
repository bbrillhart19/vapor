### Base Dockerfile to support the Vapor package ###
# NOTE: This dockerfile is not being used and is just here
# as a reference for the moment.
FROM python:3.12-slim

WORKDIR /vapor 

# See .dockerignore for which files are excluded
COPY . .

# Install the package
RUN pip install -e .
