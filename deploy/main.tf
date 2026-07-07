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
  key_name   = "opsis-aws-deployer-jamaica"
  public_key = var.deployer_public_key
}

resource "aws_default_vpc" "jamaica" {
  tags = {
    Name = "Jamaica VPC"
  }
}

# NB: do not set `description` on this security group: it was created without
# one, and changing the description forces the security group to be replaced.
resource "aws_security_group" "access_http_ssh" {
  name   = "access_jamaica"
  vpc_id = aws_default_vpc.jamaica.id

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

resource "aws_instance" "jamaica" {
  instance_type = var.instance_type
  ami           = data.aws_ami.ubuntu.id

  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.access_http_ssh.id]

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
  #   terraform apply -replace=aws_instance.jamaica
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

resource "aws_route53_record" "jamaica" {
  zone_id = data.aws_route53_zone.selected.zone_id
  name    = var.site_url
  type    = "A"
  ttl     = 300
  records = [aws_instance.jamaica.public_ip]
}
