#!/usr/bin/env bash
set -e
set -x

#
# Deploy app data
# - assumes that SSH config is set up to connect to host "jsrat1"
#
host="jsrat1"
BASEDIR=$(dirname "$0")

pushd "$BASEDIR/.."

echo "Running in $PWD"

# vector data
rsync -ravz tileserver/vector/data/ "$host:/var/www/tileserver/vector/data"
rsync -ravz tileserver/vector/fonts/ "$host:/var/www/tileserver/vector/fonts"
rsync -ravz tileserver/vector/config.json "$host:/var/www/tileserver/vector"

# raster data (tiledb arrays, served by the django backend)
rsync -ravz tileserver/raster/data/ "$host:/var/www/tileserver/raster/data"

# pixel stack data and layer metadata (served by the django backend)
rsync -ravz tileserver/stacks/ "$host:/var/www/tileserver/stacks"
rsync -avz etl/hazard_layers.csv "$host:/var/www/etl/"

# docker compose configuration
rsync -avz docker-compose.prod.yml "$host:/var/www/"
rsync -avz envs/prod "$host:/var/www/envs/"

# pull updated images and (re)start services
ssh "$host" "cd /var/www && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d"

popd
