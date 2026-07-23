terraform {
  required_version = ">= 1.10" # `use_lockfile` in the backend needs 1.10+

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Shared remote state, so state is not tied to (or lost with) one person's
  # machine. The bucket is created by the one-off configuration in
  # state-bootstrap/ - apply that first, then run `terraform init` here (or
  # `terraform init -migrate-state` if you have existing local state to move).
  backend "s3" {
    bucket       = "nismod-irv-terraform-state"
    key          = "irv-standalone/deploy/terraform.tfstate"
    region       = "eu-west-2"
    encrypt      = true
    use_lockfile = true # S3-native state locking
  }
}
