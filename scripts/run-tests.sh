#!/bin/bash
# Don't set stop on error to make sure we continue to teardown

# Extra arguments such as running a specific test
test_args=$1
# Always teardown dev services first just in case they are running
docker compose --profile dev down
# Start up the services
docker compose --profile dev up -d --wait --wait-timeout 60 &&
# Run tests
pytest --cov=vapor $test_args 
# Teardown services
docker compose --profile dev down
