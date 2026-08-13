# ─── DB Subnet Group ──────────────────────────────────────────
# Tells RDS which subnets it is allowed to run in
# We point it at our private DB subnets — never the public ones

resource "aws_db_subnet_group" "main" {
  name        = "${var.project_name}-db-subnet-group-${var.environment}"
  description = "Subnet group for car assistant RDS"
  subnet_ids  = [
    aws_subnet.private_db_a.id,
    aws_subnet.private_db_b.id
  ]
}

# ─── DB Parameter Group ───────────────────────────────────────
# A parameter group is a collection of settings for your DB engine
# We need a custom one so we can enable the pgvector extension

resource "aws_db_parameter_group" "main" {
  name        = "${var.project_name}-pg16-${var.environment}"
  family      = "postgres16"
  description = "Custom parameter group for car assistant - enables pgvector"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
    apply_method = "pending-reboot"    # ← static params need a reboot to apply
  }
}

# ─── RDS PostgreSQL Instance ──────────────────────────────────

resource "aws_db_instance" "main" {
  identifier        = "${var.project_name}-${var.environment}"
  engine            = "postgres"
  engine_version    = "16.14"
  instance_class    = "db.t3.micro"   # smallest and cheapest instance

  # Storage
  allocated_storage     = 20          # minimum 20GB
  max_allocated_storage = 20          # disable autoscaling to control costs
  storage_type          = "gp2"
  storage_encrypted     = true

  # Credentials
  db_name  = "carassistant"
  username = var.db_username
  password = var.db_password

  # Network — place it in private DB subnets
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false   # TEMPORARY — revert after schema setup

  # Parameter group
  parameter_group_name = aws_db_parameter_group.main.name

  # Backups
  backup_retention_period = 3         # keep 3 days of backups
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Cost saving settings for dev
  multi_az                = false     # single AZ — saves ~50% vs multi-AZ
  skip_final_snapshot     = true      # no snapshot when destroyed (dev only)
  deletion_protection     = false     # allow easy teardown in dev

  # Performance insights off — saves a small amount
  performance_insights_enabled = false
}