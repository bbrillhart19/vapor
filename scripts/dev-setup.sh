#!/bin/bash

# Set up dev neo4j instance
docker compose -f compose.dev.yaml up -d &&
# Populate it
python vapor/populate.py -i -f -g -G -t -l 3 --dev

echo "Dev setup complete >>>"
