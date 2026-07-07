#!/usr/bin/env bash
set -e
set -x

#
# Deploy app data
# - assumes that SSH config is set up to connect to host "jamaica"
#
host="jamaica"
BASEDIR=$(dirname "$0")

pushd "$BASEDIR/.."

echo "Running in $PWD"

# vector data
rsync -ravz tileserver/vector/data/ "$host:/var/www/tileserver/vector/data"
rsync -ravz tileserver/vector/fonts/ "$host:/var/www/tileserver/vector/fonts"
rsync -ravz tileserver/vector/config.json "$host:/var/www/tileserver/vector"

# raster data
rsync -ravz tileserver/raster/data/ "$host:/var/www/tileserver/raster/data"
rsync -ravz tileserver/raster/config.toml "$host:/var/www/tileserver/raster"

# pixel stack data
rsync -ravz tileserver/stacks/ "$host:/var/www/tileserver/stacks"
rsync -avz etl/hazard_layers.csv "$host:/var/www/etl/"

# docker compose configuration
rsync -avz docker-compose.stage.yml "$host:/var/www/"
rsync -avz envs/stage/ "$host:/var/www/envs"

# pull updated images and (re)start services
ssh "$host" "cd /var/www && docker compose -f docker-compose.stage.yml pull && docker compose -f docker-compose.stage.yml up -d"

popd
