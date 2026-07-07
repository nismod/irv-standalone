output "public_ip" {
  description = "Public IP address of the application server"
  value       = aws_instance.jamaica.public_ip
}

output "site_url" {
  description = "DNS name pointing at the application server"
  value       = aws_route53_record.jamaica.name
}
