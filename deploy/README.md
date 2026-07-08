# Deploy

The site can run on a single Linux virtual machine, with a separate database server.

The virtual machine runs several services, coordinated by docker compose
(mirroring `docker-compose.dev.yml`, without traefik or the dev database):

- Frontend React application, built using node and npm. In production this is
  stored and served as static files (HTML/JS/CSS).
- Backend Django application (`irvapp`), which serves the API - including
  raster tiles (from tiledb) and pixel data - and proxies the vector
  tileserver
- Vector tileserver, tileserver-gl-light - not exposed directly, reached by
  the backend over the compose network

The application source code is held in [this
repository](https://github.com/nismod/irv-standalone/) and this guide assumes that
it is built using node and npm locally on a development machine. It would be
possible to build directly on the server in a working directory.

To build and deploy the site:

- provision a server
- configure the server
- build and push docker images
- upload data and configuration
- load or restore data to the database
- pull and run the services

## AWS (optional)

This is optional, and only relevant if setting up on Amazon Web Services.

Server provision (and related DNS/access configuration) for AWS can be run using
[terraform](https://www.terraform.io/).

The scripts and configuration referenced below could be adapted to set up a
virtual machine or server in other environments, the AWS-specific elements are
all used to manage DNS and access.

Install the
[AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
then run:

```bash
aws configure   # one-off to set your AWS credentials
```

Install [terraform](https://www.terraform.io/) (>= 1.10).

Terraform state is stored in a shared S3 bucket, which must exist before the
main configuration can be initialised. If the bucket does not exist yet
(one-off, first person only):

```bash
cd state-bootstrap
terraform init
terraform apply  # creates the versioned, encrypted state bucket
cd ..
```

Then, from this `deploy` directory:

```bash
terraform init  # one-off; add -migrate-state if you have existing local state
terraform plan  # to see what actions will be taken in detail
terraform apply # rerun after any change to the *.tf files
```

The configuration is split across several files:

- `versions.tf` - required terraform and provider versions, and the S3 remote
  state backend
- `variables.tf` - input variables (site domain name, instance type, SSH key
  and allowed SSH source ranges, AMI filter, database sizing)
- `main.tf` - the application server: EC2 instance, key pair, security group,
  DNS record
- `database.tf` - RDS PostgreSQL database and its security group
- `outputs.tf` - outputs (server public IP, site URL, database address and
  credentials secret)
- `state-bootstrap/` - separate one-off configuration that creates the state
  bucket

All variables have working defaults. To override them, pass `-var` flags or
copy `terraform.tfvars.example` to `terraform.tfvars` (git-ignored, as it may
hold environment-specific or sensitive values) and edit. In particular,
consider restricting SSH access to a trusted network range - strongly
recommended:

```conf
# terraform.tfvars
ssh_ingress_cidr_blocks = ["192.0.2.0/24"]
```

Example SSH client config for the AWS host:

```sshconfig
Host mauritius
  HostName <terraform public_ip output>
  User ubuntu
  IdentityFile ~/.ssh/opsis-irv-mauritius
```

With that in place, you can connect directly with:

```bash
ssh mauritius
```

Or, without a local SSH config entry:

```bash
ssh -i ~/.ssh/opsis-irv-mauritius ubuntu@"$(terraform output -raw public_ip)"
```

Operational notes:

- `.terraform.lock.hcl` pins the exact provider version and is committed. It
  currently holds hashes for `linux_amd64` only: if you work on another
  platform, run e.g.
  `terraform providers lock -platform=linux_amd64 -platform=darwin_arm64`
  and commit the result.
- The root volume is configured with encryption. Applying this to an instance
  originally created without encryption **destroys and recreates the
  server** - check `terraform plan`, and be ready to re-run `provision.sh`
  and `deploy.sh` and restore data afterwards.
- The AMI lookup tracks the latest Ubuntu LTS image but the running instance
  is not replaced when a new image is released (`ignore_changes = [ami]`). To
  rebuild the server on a fresh image, run
  `terraform apply -replace=aws_instance.standalone` - note this destroys the
  server and its disk. If a planned rebuild shows the *old* AMI id being
  reused, temporarily comment out the `ignore_changes` line in `main.tf` for
  that apply to pick up the latest image.

## On-premises (optional)

This is optional, and only relevant if setting up servers on-premises.

The service requires two virtual machines with similar specifications:

1. Application server
   - exposed to internal or public network to serve the app (ports 80 and 443)
   - running Ubuntu 20.04
   - minimum resources of ~20GB disk, ~1GB RAM, 2 cores
2. Database server
   - exposed to the application server
   - running Ubuntu 20.04
   - minimum resources of ~80GB disk, ~1GB RAM, 2 cores

## VM provisioning

`provision.sh` sets up an Ubuntu LTS server to run the application:

- docker and the docker compose plugin, to run the app containers (started on
  boot; the compose services are marked `restart: unless-stopped` so they come
  back after a reboot)
- nginx as a reverse proxy terminating incoming connections, with HTTP basic
  authentication (installed from `etc/nginx/sites-available/site.conf.template`)
- Let's Encrypt ([certbot](https://certbot.eff.org/)) to acquire an SSL
  certificate and renew it automatically (via the `certbot.timer` systemd
  timer, which reloads nginx on renewal)

> This is relevant in either AWS or on-premises setup.

Copy the `deploy` directory to the server (or clone this repository there)

```bash
rsync -Pavr --exclude='*/.terraform/*' deploy mauritius:'~/'
```

Then run:

```bash
SITE_DOMAIN=mauritius.infrastructureresilience.org \
CERTBOT_EMAIL=you@example.org \
  bash deploy/provision.sh
```

Notes:

- DNS for `SITE_DOMAIN` must already resolve to the server, or the Let's
  Encrypt HTTP challenge fails. On AWS, run `terraform apply` first - it
  creates the DNS record. If DNS is not ready, leave `CERTBOT_EMAIL` unset and
  the script prints the `certbot` command to run later.
- The script is idempotent: rerunning it is safe.
- docker group membership takes effect at next login, so log out and in (or
  `newgrp docker`) before running `docker compose` as your own user.

## Database provisioning

`provision-database-server.sh` contains installation instructions for an Ubuntu
20.04 server to install a PostgreSQL database server with the PostGIS extension.

> This is only relevant on-premises. On AWS, terraform provisions an RDS
> PostgreSQL database instead (see `database.tf`) - do not run the script.

On AWS, get the database address from terraform and save as `PGHOST` in the `.env` file:

```bash
terraform output -raw database_address
```

On AWS, the database master password is generated and stored by RDS in AWS
Secrets Manager; it is not in terraform configuration or state. To retrieve
it:

```bash
aws secretsmanager get-secret-value \
  --secret-id "$(terraform output -raw database_master_user_secret_arn)" \
  --query SecretString --output text
```

The database only accepts connections from the application server's security
group, so connect from the application server (over SSH), with `PGHOST` set to
the `database_address` terraform output.

Enable PostGIS once per database:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

If setting up from scratch, login as postgres, then set up user with database privileges.

```sql
CREATE ROLE irv_rw;
GRANT USAGE, CREATE ON SCHEMA public to irv_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO irv_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO irv_rw;

CREATE USER irvadmin WITH PASSWORD 'replace-me';
GRANT irv_rw TO irvadmin;
```


## Basic authentication

The app can be configured to use [HTTP Basic
Authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication)
to authenticate users. In this case, the connection must always use HTTPS, to
ensure that credentials are protected.

The user accounts are stored in a text file on the server, which is used by the
Nginx server, which terminates all connections and reverse-proxies connections
to the other app services. See the
[Nginx docs](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/)
for more on this configuration.

The password file lives at `/etc/nginx/.htpasswd` (referenced by the site
config, and created empty by `provision.sh`). Create it if it doesn't already
exist:

```bash
sudo touch /etc/nginx/.htpasswd
```

### Add a user account

Optionally use the command-line password generation utility, `pwgen`, to generate
passwords. E.g. run the following to generate three 16-character passwords:

    pwgen -N3 16

To add or update a user in the password file (will prompt for password):

```bash
sudo htpasswd -B /etc/nginx/.htpasswd new-username
```

Test that it worked by visiting the site in a private tab, and entering the new
username and password when prompted.

### Remove a user account

Edit the file `/etc/nginx/.htpasswd` to remove the line with the relevant username, or run:

    sudo htpasswd -D /etc/nginx/.htpasswd username

Test that deletion worked by visiting the site in a private tab, and entering
the old username and password when prompted, which should fail to authenticate.

### Certificate renewal

Certificates are renewed automatically: `provision.sh` sets up certbot with
the nginx plugin, and the `certbot.timer` systemd timer renews the certificate
before its 90-day expiry and reloads nginx, with no downtime. If the
certificate is outdated, users will see a security warning in the browser when
they visit the site.

To check that auto-renewal is working (over SSH on the server):

```bash
systemctl list-timers certbot.timer   # next scheduled run
sudo certbot renew --dry-run          # test a renewal without changing anything
```

To renew manually (nginx does not need to be stopped):

```bash
sudo certbot renew
```

Then visit the site (hard browser refresh) to check the certificate comes
through.

## Backend environment file

The backend (django) container reads its configuration from an environment
file which holds secrets and environment-specific values, so it must **not**
be committed to this repository (the `envs` directory is git-ignored). It
lives at `envs/prod/.backend.env` locally (`envs/stage/.backend.env` for
staging) and is uploaded to the server by `deploy.sh` / `deploy_stage.sh`.

Expected contents, to be replaced with actual details:

```conf
# Database connection
PGHOST=localhost
PGDATABASE=irvdev
PGUSER=docker
PGPASSWORD=docker

# Django settings
# generate a secret key with e.g.:
#   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=mauritius.infrastructureresilience.org
CSRF_TRUSTED_ORIGINS=https://mauritius.infrastructureresilience.org
```

Testing database connection:

```bash
cd /var/www/
set -a
source ./envs/prod/.backend.env  # to use app connection details
# source ./envs/prod/.dbrestore.env  # to use admin connection details
set +a
# if needed:
# sudo apt install postgresql-client
psql
```

Restore a database dump:

```bash
pg_restore -cC -d postgres /path/to/backup.dump
```

## Deployment

Create a GitHub access token with `read:packages` - use this to log into the
GitHub package registry. For more information, see these [instructions for
authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
and use a token with `read:packages` scope to read from the GHCR.

On remote, to first start the application:

```bash
# on remote
docker login ghcr.io  # use GitHub username for username, GitHub access token for password
cd /var/www
docker compose -f docker-compose.prod.yml up -d
```

Run `deploy/deploy_stage.sh` to upload data and docker-compose config, pull the
published images and (re)start the services.

### Manage staging/production


The docker compose setup runs the frontend, the django backend and the vector
tileserver. Frontend and backend are exposed on high-numbered ports bound to
localhost; the vector tileserver is reached by the backend over the compose
network.

[Nginx](https://nginx.org/en/) is used as a reverse-proxy to terminate incoming
connections and pass them on to the containerised services.

Find example configuration files in `./etc/nginx/sites-available`. On the
server, the relevant file should be symlinked to `/etc/nginx/sites-enabled`.

See [certbot docs](https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal)
for instructions on setting up or renewing SSL certificates.

### Publishing docker images

For pushing to the GitHub container registry, you will need to follow these
[instructions for authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) and use a token with `write:packages` scope.

Build and publish all images (versions as set in `docker-compose.prod.yml`;
the backend image is built from `./irvapp`):

```bash
# Build images locally
docker compose -f docker-compose.prod.yml build

# Push to GitHub container registry
docker push ghcr.io/nismod/jsrat-frontend:0.1
docker push ghcr.io/nismod/jsrat-backend:0.3
docker push ghcr.io/nismod/jsrat-vector-tileserver:0.1
```

### Updating a service

Update a specific image, then build and push:

```bash
# Edit the image version in `docker-compose.prod.yml`
# in this example it's on line 33:
#     image: ghcr.io/nismod/jsrat-frontend:0.1

# Build
docker compose -f docker-compose.prod.yml build frontend

# Push
docker push ghcr.io/nismod/jsrat-frontend:0.1
```

Run `deploy.sh` to update the docker-compose config on the server, pull
images and restart services.

Alternatively, on the remote server, pull the image, then restart the
specific service:

```bash
# Pull image
docker pull ghcr.io/nismod/jsrat-frontend:0.1

# Restart service
docker compose -f docker-compose.prod.yml up -d frontend
```
