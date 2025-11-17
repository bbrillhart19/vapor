#!/bin/bash

# Get limit from args
limit=$1
if [ $limit == "" ]; then
    limit=(3)
fi

# Start the dev services
bash scripts/dev/start.sh

# Populate neo4j
VAPOR_ENV=dev.env python vapor/populate.py \
    -i -f -g -G -d -l $limit \
    --embed game-descriptions

echo "Vapor dev setup complete >>>"
