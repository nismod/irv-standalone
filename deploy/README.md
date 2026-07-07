# Deploy

The site can run on a single Linux virtual machine, with a separate database server.

The virtual machine runs several services, coordinated by docker-compose:

- Frontend React application, built using node and npm. In production this is
  stored and served as static files (HTML/JS/CSS).
- Vector tileserver, tileserver-gl-light, depends on node
- Raster tileserver, terracotta, depends on gunicorn and Python 3.10
- Backend Python application, depends on uvicorn, fastapi and Python 3.10

The application source code is held in [this
repository](https://github.com/nismod/irv-jamaica/) and this guide assumes that
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
  `terraform apply -replace=aws_instance.jamaica` - note this destroys the
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

`provision.sh` contains installation instructions for an Ubuntu 20.04 server to
install docker and docker-compose.

> This is relevant in either AWS or on-premises setup.

## Database provisioning

`provision-database-server.sh` contains installation instructions for an Ubuntu
20.04 server to install a PostgreSQL database server with the PostGIS extension.

> This is only relevant on-premises. On AWS, terraform provisions an RDS
> PostgreSQL database instead (see `database.tf`) - do not run the script.

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
the `database_address` terraform output. Enable PostGIS once per database:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

## Basic authentication

The J-SRAT app can be configured to use [HTTP Basic
Authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication)
to authenticate users. In this case, the connection must always use HTTPS, to
ensure that credentials are protected.

The user accounts are stored in a text file on the server, which is used by the
Nginx server, which terminates all connections and reverse-proxies connections
to the other app services. See the
[Nginx docs](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/)
for more on this configuration.

Create a password file for HTTP Basic Authentication if it doesn't already
exist:

```bash
sudo touch /var/www/auth/.htpasswd
```

### Add a user account

Optionally use the command-line password generation utility, `pwgen`, to generate
passwords. E.g. run the following to generate three 16-character passwords:

    pwgen -N3 16

To add or update a user in the password file (will prompt for password):

```bash
sudo htpasswd -B /var/www/auth/.htpasswd new-username
```

Test that it worked by visiting the site in a private tab, and entering the new
username and password when prompted.

### Remove a user account

Edit the file `/etc/nginx/.htpasswd` to remove the line with the relevant username, or run:

    sudo htpasswd -D /etc/nginx/.htpasswd username

Test that deletion worked by visiting the site in a private tab, and entering
the old username and password when prompted, which should fail to authenticate.

### Certificate renewal

The server can be configured to manage its own SSL certificate, and should
auto-renew every 90 days, but this may fail. If the certificate is outdated,
users will see a security warning in the browser when they visit the site.

To renew:

1. Log in to the J-SRAT server via SSH
2. Stop the NGINX server process: `service nginx stop`
3. Renew the certificate: `sudo certbot renew`
4. Start NGINX again: `service nginx start`
5. Visit the site (hard browser refresh) to check the certificate comes through.

## Database connection

The `PG*` variables for connection to database, to be replaced with actual details:

```conf
PGDATABASE=jamaica
PGUSER=docker
PGPASSWORD=docker
PGHOST=localhost
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

Run `deploy.sh` to upload data and docker-compose config.

### Manage production

On remote, to first start the application:

```bash
cd /var/www
docker compose -f docker-compose.prod.yml up -d
```

For pulling from the GitHub container registry (GHCR), you will need to follow these
[instructions for authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
and use a token with `read:packages` scope to read from the GHCR.

The docker compose setup runs frontend, backend, vector and raster tileservers
and exposes these on high-numbered ports within the machine.

[Nginx](https://nginx.org/en/) is used as a reverse-proxy to terminate incoming
connections and pass them on to the containerised services.

Find example configuration files in `./etc/nginx/sites-available`. On the
server, the relevant file should be symlinked to `/etc/nginx/sites-enabled`.

See [certbot docs](https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal)
for instructions on setting up or renewing SSL certificates.

### Publishing docker images

For pushing to the GitHub container registry, you will need to follow these
[instructions for authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) and use a token with `write:packages` scope.

Build and publish all images:

```bash
# Build images locally
docker compose -f docker-compose.prod.yml build

# Push to GitHub container registry
docker push ghcr.io/nismod/jsrat-frontend:0.1
docker push ghcr.io/nismod/jsrat-backend:0.2
docker push ghcr.io/nismod/jsrat-vector-tileserver:0.1
docker push ghcr.io/nismod/jsrat-raster-tileserver:0.1
```

```bash
docker push ghcr.io/nismod/jsrat-frontend:0.1
docker push ghcr.io/nismod/jsrat-backend:0.2
docker push ghcr.io/nismod/jsrat-vector-tileserver:0.1
docker push ghcr.io/nismod/jsrat-raster-tileserver:0.1
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

Run `deploy.sh` to update the docker-compose config on the server.

On the remote server, pull the image, then restart the specific service:

```bash
# Pull image
docker pull ghcr.io/nismod/jsrat-frontend:0.1

# Restart service
docker compose up -d frontend
```
