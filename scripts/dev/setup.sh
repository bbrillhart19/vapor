#!/bin/bash

# Start services
bash scripts/dev/start.sh
# Populate neo4j
python vapor/populate.py -i -f -g -G -d -l 3 \
    --embed game-descriptions --dev

echo "Vapor dev setup complete >>>"
