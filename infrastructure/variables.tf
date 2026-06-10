variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "car-assistant"
}

variable "db_username" {
  description = "Master username for RDS PostgreSQL"
  type        = string
  default     = "caradmin"
}

variable "db_password" {
  description = "Master password for RDS PostgreSQL"
  type        = string
  sensitive   = true   # ← Terraform will never print this in logs
}

variable "developer_ip" {
  description = "Developer IP address for bastion SSH access"
  type        = string
  default     = "83.7.144.234/32"
}