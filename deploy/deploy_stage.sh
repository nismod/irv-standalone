#!/usr/bin/env bash
set -e
set -x

#
# Deploy app data
# - assumes that SSH config is set up to connect to host "mauritius"
#
host="${1:-mauritius}"
BASEDIR=$(dirname "$0")

pushd "$BASEDIR/.."

echo "Running in $PWD"

# vector data
rsync -rvz tileserver/vector/ "$host:/var/www/tileserver/vector"

# raster data
rsync -rvz tileserver/raster/ "$host:/var/www/tileserver/raster"

# pixel stack data
rsync -rvz tileserver/stacks/ "$host:/var/www/tileserver/stacks"
rsync -vz etl/hazard_layers.csv "$host:/var/www/etl/"

# docker compose configuration
rsync -vz docker-compose.stage.yml "$host:/var/www/"
rsync -vz envs/stage/ "$host:/var/www/envs"

# pull updated images and (re)start services
ssh "$host" "cd /var/www && docker compose -f docker-compose.stage.yml pull && docker compose -f docker-compose.stage.yml up -d"

popd
