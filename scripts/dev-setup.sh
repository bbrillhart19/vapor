#!/bin/bash

# Set up dev neo4j instance
docker compose -f compose.dev.yaml up -d &&
# Populate it
python vapor/populate.py -i -f -g -G -d -l 3 \
    --embed game-descriptions --dev

echo "Dev setup complete >>>"
