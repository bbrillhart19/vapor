#!/bin/bash
# Extra arguments such as running a specific test
test_args=$1
# Always teardown neo4j-dev first just in case it's running
docker compose -f compose.dev.yaml down
# Spin up neo4j
docker compose -f compose.dev.yaml up -d && 
# Run tests
pytest --cov=vapor $test_args 
# Teardown neo4j
docker compose -f compose.dev.yaml down
