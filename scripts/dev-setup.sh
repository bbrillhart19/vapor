#!/bin/bash

# Set up dev neo4j instance
docker compose -f compose.dev.yaml up -d &&
# Populate it
python vapor/populate.py -i -f -g -G --dev

echo "Dev setup complete >>>"
