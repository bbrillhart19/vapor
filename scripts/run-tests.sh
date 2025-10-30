#!/bin/bash
# Extra arguments such as running a specific test
test_args=$1
# Spin up neo4j and use helper script to wait for connection
docker compose -f compose.dev.yaml up -d && 
python tests/helpers/verify_neo4j_connect.py &&
# Run tests
pytest $test_args --cov=vapor --log-cli-level info
# Teardown neo4j
docker compose -f compose.dev.yaml down
