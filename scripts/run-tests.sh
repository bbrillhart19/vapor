#!/bin/bash
# Extra arguments such as running a specific test
test_args=$1
# Always teardown neo4j-dev first just in case it's running
docker compose -f compose.dev.yaml down &&
# Spin up neo4j and use helper script to wait for connection
docker compose -f compose.dev.yaml up -d && 
python tests/helpers/verify_neo4j_connect.py &&
# Run tests
pytest --cov=vapor $test_args 
# Teardown neo4j
docker compose -f compose.dev.yaml down
