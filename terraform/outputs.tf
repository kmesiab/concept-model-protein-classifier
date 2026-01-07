output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.api.repository_url
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.api.name
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "api_url" {
  description = "URL of the API endpoint"
  value       = "https://${var.api_subdomain}.${var.domain_name}"
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions IAM role"
  value       = data.aws_iam_role.github_actions.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for ECS tasks"
  value       = aws_cloudwatch_log_group.ecs_logs.name
}

output "alb_target_group_arn" {
  description = "ARN of the ALB target group"
  value       = aws_lb_target_group.ecs.arn
}

output "jwt_secret_arn" {
  description = "ARN of the JWT secret in AWS Secrets Manager"
  value       = aws_secretsmanager_secret.jwt_secret_key.arn
  sensitive   = true
}

output "jwt_secret_name" {
  description = "Name of the JWT secret in AWS Secrets Manager"
  value       = aws_secretsmanager_secret.jwt_secret_key.name
}
