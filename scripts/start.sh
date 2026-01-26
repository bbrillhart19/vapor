#!/bin/bash
set -e

source ./.env

echo "Starting Vapor services ($RESOURCE_PROFILE)..."

compose_files="-f compose.yaml"
if [[ $RESOURCE_PROFILE != "cpu" ]]; then
    compose_files="$compose_files -f compose.$RESOURCE_PROFILE.yaml"
fi

docker compose $compose_files --profile default up -d --wait --wait-timeout 60
