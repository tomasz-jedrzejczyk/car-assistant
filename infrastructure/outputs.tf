output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "private_app_subnet_ids" {
  description = "Private app subnet IDs"
  value       = [aws_subnet.private_app_a.id, aws_subnet.private_app_b.id]
}

output "private_db_subnet_ids" {
  description = "Private DB subnet IDs"
  value       = [aws_subnet.private_db_a.id, aws_subnet.private_db_b.id]
}

output "sg_app_id" {
  description = "App security group ID"
  value       = aws_security_group.app.id
}

output "sg_db_id" {
  description = "DB security group ID"
  value       = aws_security_group.db.id
}

output "sg_redis_id" {
  description = "Redis security group ID"
  value       = aws_security_group.redis.id
}

output "db_endpoint" {
  description = "RDS PostgreSQL endpoint to connect to"
  value       = aws_db_instance.main.endpoint
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "db_username" {
  description = "Database master username"
  value       = aws_db_instance.main.username
}

output "bastion_public_ip" {
  description = "Bastion host Elastic IP — stays same after stop/start"
  value       = aws_eip.bastion.public_ip
}

output "api_url" {
  description = "API Gateway URL — use this to call the API"
  value       = aws_apigatewayv2_stage.main.invoke_url
}