#!/bin/bash
set -e

source ./.env

echo "Shutting down Vapor services ($RESOURCE_PROFILE)..."
docker compose --profile default --profile $RESOURCE_PROFILE down
