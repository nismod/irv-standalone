variable "site_url" {
  description = "Fully-qualified domain name for the site, created as a Route53 A record"
  type        = string
  default     = "jamaica.infrastructureresilience.org"
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
    ignore_changes on aws_instance.jamaica).
  EOT
  type        = string
  default     = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
}

variable "deployer_public_key" {
  description = "SSH public key granted access to the instance"
  type        = string
  default     = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAjX5yhc7GWROTVOM8r92rO6MEUyKt/JfTCQzCY/lNi9 opsis-aws-jamaica"
}

variable "ssh_ingress_cidr_blocks" {
  description = <<-EOT
    CIDR blocks allowed to reach SSH (port 22). Strongly recommended to
    restrict this to a trusted IP range or VPN rather than the whole internet.
  EOT
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
