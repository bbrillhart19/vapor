#!/bin/bash

# Teardown dev services
echo "Shutting down Vapor dev services..."
docker compose -f compose.dev.yaml down
