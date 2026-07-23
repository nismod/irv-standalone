variable "site_url" {
  description = "Fully-qualified domain name for the site, created as a Route53 A record"
  type        = string
  default     = "mauritius.infrastructureresilience.org"
}

variable "route53_zone_name" {
  description = "Name of the existing Route53 hosted zone that contains the site record"
  type        = string
  default     = "infrastructureresilience.org."
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-west-2"
}

variable "instance_type" {
  description = "AWS EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ubuntu_ami_name_filter" {
  description = <<-EOT
    Name filter used to pick the most recent Canonical Ubuntu AMI for new
    instances. Changing this does not replace a running instance (see
    ignore_changes on aws_instance.standalone).
  EOT
  type        = string
  default     = "ubuntu/images/hvm-ssd-gp3/ubuntu-resolute-26.04-amd64-server-*"
}

variable "deployer_public_key" {
  description = "SSH public key granted access to the instance"
  type        = string
  default     = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGSG7VjfFHbwV9WEWPz1dUiiSrwz/f26IegBWW4kHbat opsis-irv-mauritius"
}

variable "deployer_public_key_name" {
  default = "opsis-irv-mauritius"
}

variable "root_volume_size_gb" {
  description = "Size of the application server root EBS volume in GB"
  type        = number
  default     = 20
}

variable "db_instance_class" {
  description = "RDS instance class for the PostgreSQL database"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial RDS storage in GB (autoscales up to db_max_allocated_storage)"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Upper limit in GB for RDS storage autoscaling"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Name of the initial database created on the RDS instance"
  type        = string
  default     = "irvdev"
}

variable "db_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "postgres"
}

variable "ssh_ingress_cidr_blocks" {
  description = <<-EOT
    CIDR blocks allowed to reach SSH (port 22). Strongly recommended to
    restrict this to a trusted IP range or VPN rather than the whole internet.
  EOT
  type        = list(string)
  default     = ["129.67.116.0/22", "163.1.0.0/16"]
}

variable "vpc_name" {
  default = "Mauritius Staging VPC"
}

variable "vpc_cidr_block" {
  description = "CIDR block for the dedicated VPC"
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidr_block" {
  description = "CIDR block for the public subnet hosting the app instance"
  type        = string
  default     = "10.42.1.0/24"
}

variable "db_subnet_cidr_blocks" {
  description = "CIDR blocks for private database subnets in distinct AZs"
  type        = list(string)
  default     = ["10.42.10.0/24", "10.42.11.0/24"]
}
