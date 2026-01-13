#!/bin/bash
set -e

source ./.env

echo "Starting Vapor services ($RESOURCE_PROFILE)..."
docker compose --profile default --profile $RESOURCE_PROFILE up -d --wait --wait-timeout 60
