#!/usr/bin/env bash
set -euo pipefail

#
# Provision virtual machine
# - assuming OS is Ubuntu LTS (20.04 or later)
# - assuming this script is run as a user in groups sudo and jsrat_admin
# - assuming it is run from a checkout (or copy) of the deploy directory, so
#   that ./etc/nginx/sites-available/site.conf.template is alongside it
#
# Sets up:
# - docker and the docker compose plugin, to run the app containers
# - nginx as a reverse proxy for the app services, with HTTP basic auth
# - Let's Encrypt (certbot) to acquire an SSL certificate and auto-renew it
#
# Configuration (environment variables):
#   SITE_DOMAIN   domain to serve and request a certificate for
#                 (default: jamaica.infrastructureresilience.org)
#   CERTBOT_EMAIL email for Let's Encrypt registration and expiry notices;
#                 if unset, certificate setup is skipped and printed as a
#                 manual follow-up step
#

SITE_DOMAIN="${SITE_DOMAIN:-jamaica.infrastructureresilience.org}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"
BASEDIR=$(cd "$(dirname "$0")" && pwd)

NGINX_TEMPLATE="$BASEDIR/etc/nginx/sites-available/site.conf.template"
if [ ! -f "$NGINX_TEMPLATE" ]; then
  echo "Cannot find $NGINX_TEMPLATE - run this script from a copy of the deploy directory" >&2
  exit 1
fi

#
# Install helper apt packages, nginx and certbot
#
sudo apt-get update
sudo apt-get install -y \
  ca-certificates curl gnupg \
  apache2-utils \
  nginx \
  certbot python3-certbot-nginx

#
# Install docker and the docker compose plugin
#
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg |
  sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" |
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start docker now and on boot - containers marked `restart: unless-stopped`
# in the compose file then come back automatically after a reboot
sudo systemctl enable --now docker

# Set up current user with docker
getent group docker > /dev/null || sudo groupadd docker
sudo usermod -aG docker "$USER"
# NB: docker group membership takes effect at next login; run `newgrp docker`
# to use docker without sudo in the current shell

#
# Set up data directories
#
getent group jsrat_admin > /dev/null || sudo groupadd jsrat_admin
sudo mkdir -p /var/www/html
sudo mkdir -p /var/www/tileserver/raster/data
sudo mkdir -p /var/www/tileserver/vector/data
sudo mkdir -p /var/www/tileserver/stacks
sudo mkdir -p /var/www/etl
sudo chown -R :jsrat_admin /var/www/
sudo chmod -R 775 /var/www/tileserver/ /var/www/etl/

#
# Set up nginx as a reverse proxy for the app services
#
# Password file for HTTP basic auth - add users with:
#   sudo htpasswd -B /etc/nginx/.htpasswd username
sudo touch /etc/nginx/.htpasswd

# Install the site config. This bootstrap version serves plain HTTP; certbot
# rewrites the installed copy below to add SSL termination and redirect.
sed "s/DOMAIN_PLACEHOLDER/${SITE_DOMAIN}/g" "$NGINX_TEMPLATE" |
  sudo tee "/etc/nginx/sites-available/${SITE_DOMAIN}" > /dev/null
sudo ln -sf "/etc/nginx/sites-available/${SITE_DOMAIN}" "/etc/nginx/sites-enabled/${SITE_DOMAIN}"
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx

#
# Let's Encrypt SSL certificate
#
# `certbot --nginx` proves control of the domain over HTTP (so the DNS record
# must already point at this server), rewrites the site config to terminate
# SSL and redirect HTTP to HTTPS, and installs a systemd timer
# (certbot.timer) which renews the certificate automatically before expiry
# and reloads nginx.
if [ -n "$CERTBOT_EMAIL" ]; then
  sudo certbot --nginx \
    --domain "$SITE_DOMAIN" \
    --email "$CERTBOT_EMAIL" \
    --agree-tos --no-eff-email --non-interactive --redirect
  echo "Certificate installed. Auto-renewal timer status:"
  systemctl list-timers certbot.timer --no-pager
else
  echo "CERTBOT_EMAIL not set - skipping certificate setup."
  echo "Once DNS for ${SITE_DOMAIN} points at this server, run:"
  echo "  sudo certbot --nginx -d ${SITE_DOMAIN} --redirect"
fi
