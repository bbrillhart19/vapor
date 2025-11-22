#!/bin/bash

# Start up dev services
echo "Starting up Vapor dev services..."
docker compose -f compose.dev.yaml up -d
