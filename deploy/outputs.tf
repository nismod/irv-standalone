output "public_ip" {
  description = "Public IP address of the application server"
  value       = aws_instance.standalone.public_ip
}

output "site_url" {
  description = "DNS name pointing at the application server"
  value       = aws_route53_record.standalone.name
}

output "database_address" {
  description = "Hostname of the RDS database (resolves inside the VPC only)"
  value       = aws_db_instance.database.address
}

output "database_master_user_secret_arn" {
  description = "Secrets Manager secret holding the database master user password"
  value       = aws_db_instance.database.master_user_secret[0].secret_arn
}
