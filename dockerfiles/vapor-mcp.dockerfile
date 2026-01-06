### Dockerfile to support Vapor MCP (+ core) ###
FROM python:3.12-slim

WORKDIR /app

# See .dockerignore for which files are excluded
COPY ./pyproject.toml ./pyproject.toml
COPY ./vapor/__init__.py ./vapor/__init__.py
COPY ./vapor/core ./vapor/core
COPY ./vapor/svc/__init__.py ./vapor/svc/__init__.py
COPY ./vapor/svc/mcp ./vapor/svc/mcp

# Install the package
RUN pip install -e .[svc]
