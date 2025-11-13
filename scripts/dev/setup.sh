#!/bin/bash

# Populate neo4j
VAPOR_ENV=dev.env python vapor/populate.py \
    -i -f -g -G -d -l 3 \
    --embed game-descriptions

echo "Vapor dev setup complete >>>"
