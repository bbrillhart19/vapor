#!/bin/bash
# NOTE: Apparently this messes neo4j up on Mac?
test_args=$1


docker compose -f compose.dev.yaml up -d
# docker compose up -d

pytest $test_args --cov=vapor --log-cli-level info

docker compose -f compose.dev.yaml down
# docker compose down
