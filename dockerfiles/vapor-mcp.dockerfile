### Base Dockerfile to support the Vapor package ###
# NOTE: This dockerfile is not being used and is just here
# as a reference for the moment.
# TODO: Ollama needs to be installed for embedding model?
FROM python:3.12-slim

WORKDIR /app

# See .dockerignore for which files are excluded
COPY ./pyproject.toml ./pyproject.toml
COPY ./vapor/__init__.py ./vapor/__init__.py
COPY ./vapor/core ./vapor/core
COPY ./vapor/svc/__init__.py ./vapor/svc/__init__.py
COPY ./vapor/svc/mcp ./vapor/svc/mcp

# NOTE: Need to copy environment file in, probably shouldn't need to
COPY ./.env ./.env

# Install the package
RUN pip install -e .[svc]
