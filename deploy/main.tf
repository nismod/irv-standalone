#
# Server provision for AWS deployment (optional, see README.md): EC2 instance
# with SSH key pair and security group, and a Route53 DNS record.
#
# Variables are declared in variables.tf, provider/backend requirements in
# versions.tf, outputs in outputs.tf.
#

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "irv-standalone"
      ManagedBy = "terraform"
    }
  }
}

#
# EC2 Connection
# Keypair, VPC, Security Group
#

resource "aws_key_pair" "deployer" {
  key_name   = var.deployer_public_key_name
  public_key = var.deployer_public_key
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_default_vpc" "standalone" {
  tags = {
    Name = "Default VPC"
  }
}

resource "aws_vpc" "standalone" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = var.vpc_name
  }
}
resource "aws_internet_gateway" "standalone" {
  vpc_id = aws_vpc.standalone.id

  tags = {
    Name = "${var.vpc_name} IGW"
  }
}

resource "aws_subnet" "app_public" {
  vpc_id                  = aws_vpc.standalone.id
  cidr_block              = var.public_subnet_cidr_block
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.vpc_name} App Public"
  }
}

resource "aws_subnet" "db_private" {
  count = length(var.db_subnet_cidr_blocks)

  vpc_id            = aws_vpc.standalone.id
  cidr_block        = var.db_subnet_cidr_blocks[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.vpc_name} DB Private ${count.index + 1}"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.standalone.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.standalone.id
  }

  tags = {
    Name = "${var.vpc_name} Public Routes"
  }
}

resource "aws_route_table_association" "app_public" {
  subnet_id      = aws_subnet.app_public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "access_vpc" {
  name   = "access_mauritius"
  vpc_id = aws_vpc.standalone.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_ingress_cidr_blocks
  }
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

#
# EC2 Instance
#

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = [var.ubuntu_ami_name_filter]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "standalone" {
  instance_type = var.instance_type
  ami           = data.aws_ami.ubuntu.id

  key_name                    = aws_key_pair.deployer.key_name
  subnet_id                   = aws_subnet.app_public.id
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.access_vpc.id]

  # Encrypted root volume. NB: enabling encryption on an instance that was
  # created without it forces the instance to be destroyed and recreated -
  # check `terraform plan` and be ready to re-run provisioning and deployment
  # (provision.sh, deploy.sh) before applying.
  root_block_device {
    encrypted   = true
    volume_type = "gp3"
    volume_size = var.root_volume_size_gb
  }

  # Require IMDSv2 for instance metadata requests
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  # The AMI data source above tracks the most recent Ubuntu image, which
  # changes every few weeks; without ignore_changes, any `terraform apply`
  # after a new image release would destroy and recreate the server. To move
  # an existing server to a new AMI deliberately, run:
  #   terraform apply -replace=aws_instance.standalone
  lifecycle {
    ignore_changes = [ami]
  }

  tags = {
    Name = "${var.site_url} ${var.instance_type}"
  }
}

#
# DNS
#

data "aws_route53_zone" "selected" {
  name = var.route53_zone_name
}

resource "aws_route53_record" "standalone" {
  zone_id = data.aws_route53_zone.selected.zone_id
  name    = var.site_url
  type    = "A"
  ttl     = 300
  records = [aws_instance.standalone.public_ip]
}
