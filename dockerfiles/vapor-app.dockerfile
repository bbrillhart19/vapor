### Dockerfile to support Vapor MCP (+ core) ###
FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update -y && apt-get install curl -y

# Copy relevant files for application layer
COPY ./pyproject.toml ./pyproject.toml
COPY ./vapor/__init__.py ./vapor/__init__.py
COPY ./vapor/core ./vapor/core
COPY ./vapor/app ./vapor/app

# Install the package
RUN pip install -e .[app]
