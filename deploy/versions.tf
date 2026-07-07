terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Recommended: keep state in a shared, versioned, encrypted S3 bucket rather
  # than on one person's machine. Create the bucket (with versioning enabled)
  # once, then uncomment this block and run `terraform init -migrate-state`.
  #
  # backend "s3" {
  #   bucket       = "<your-terraform-state-bucket>"
  #   key          = "irv-standalone/deploy/terraform.tfstate"
  #   region       = "eu-west-2"
  #   encrypt      = true
  #   use_lockfile = true # S3-native state locking, requires Terraform >= 1.10
  # }
}
