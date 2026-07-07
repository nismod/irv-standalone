#
# One-off bootstrap for the terraform remote state bucket.
#
# The main configuration in ../ stores its state in S3 (see ../versions.tf),
# but that bucket has to exist before `terraform init` can use it. Apply this
# configuration once, with local state, to create it:
#
#   cd deploy/state-bootstrap
#   terraform init
#   terraform apply
#
# The bootstrap's own state stays local (and git-ignored). The bucket is the
# only thing it manages, so losing that state is low-cost: the bucket can be
# recovered with `terraform import aws_s3_bucket.terraform_state <name>`.
#

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "aws_region" {
  description = "AWS region for the state bucket (match the backend in ../versions.tf)"
  type        = string
  default     = "eu-west-2"
}

variable "state_bucket_name" {
  description = "Globally-unique name for the terraform state bucket (match the backend in ../versions.tf)"
  type        = string
  default     = "nismod-irv-terraform-state"
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "irv-standalone"
      ManagedBy = "terraform"
    }
  }
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = var.state_bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

# Versioning keeps a history of state files, protecting against corruption
# or accidental deletion
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "state_bucket" {
  description = "Name of the terraform state bucket"
  value       = aws_s3_bucket.terraform_state.id
}
