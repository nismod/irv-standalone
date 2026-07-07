#
# Database: RDS PostgreSQL (PostGIS is available via CREATE EXTENSION).
#
# The master user password is generated and stored by RDS in AWS Secrets
# Manager (manage_master_user_password), so it never appears in terraform
# configuration or state. See README.md ("Database provisioning") for how to
# retrieve it and connect.
#

resource "aws_security_group" "database" {
  name        = "access_database"
  description = "Allow PostgreSQL access from the application server"
  vpc_id      = aws_default_vpc.standalone.id

  ingress {
    description     = "PostgreSQL from application server"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.access_http_ssh.id]
  }
}

resource "aws_db_instance" "database" {
  identifier = "mauritius-database"

  engine         = "postgres"
  engine_version = "16" # major version only: minor upgrades apply automatically

  instance_class        = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name                     = var.db_name
  username                    = var.db_username
  manage_master_user_password = true

  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = false

  backup_retention_period   = 7
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "mauritius-database-final"

  tags = {
    Name = "mauritius-database"
  }
}
