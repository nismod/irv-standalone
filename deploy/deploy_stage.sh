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
rsync -rvz --chmod=D2770,F640 envs/stage/ "$host:/var/www/envs/"

# Take a database backup before running this script for a schema-changing release.
# Run release commands in the newly pulled image; stop if either fails.
ssh "$host" 'bash -se' <<'REMOTE'
cd /var/www
docker compose -f docker-compose.stage.yml pull
docker compose -f docker-compose.stage.yml run --rm --no-deps -T django python manage.py migrate --noinput
docker compose -f docker-compose.stage.yml run --rm --no-deps -T django python manage.py collectstatic --noinput
docker compose -f docker-compose.stage.yml up -d --no-build
REMOTE

popd
