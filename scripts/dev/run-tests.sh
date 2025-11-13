#!/bin/bash

# Extra arguments such as running a specific test
test_args=$1
# Always teardown dev services first just in case they are running
bash scripts/dev/quit.sh
# Start up the services
bash scripts/dev/start.sh &&
# Run tests
pytest --cov=vapor $test_args 
# Teardown services
bash scripts/dev/quit.sh
