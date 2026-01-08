# GitHub Actions OIDC Role - Reference to existing role
# This role already exists in AWS and should not be managed by Terraform.
# The existing role has carefully crafted granular permissions that are managed
# outside of this Terraform configuration to maintain separation of concerns.
# Terraform only needs to reference the role's ARN for KMS policies and outputs.
data "aws_iam_role" "github_actions" {
  name = "github-actions-terraform"
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "protein-classifier-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "protein-classifier-ecs-task-execution-role"
    Description = "ECS task execution role for pulling images and logging"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role (for application permissions)
resource "aws_iam_role" "ecs_task_role" {
  name = "protein-classifier-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "protein-classifier-ecs-task-role"
    Description = "ECS task role for application runtime permissions"
  }
}

# Policy for ECS tasks (CloudWatch Logs)
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "protein-classifier-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogsAccess"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.ecs_logs.arn}:*"
      },
      {
        Sid    = "DynamoDBAccessForAPIKeys"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:DescribeTable"
        ]
        Resource = [
          aws_dynamodb_table.api_keys.arn,
          "${aws_dynamodb_table.api_keys.arn}/index/*",
          aws_dynamodb_table.user_sessions.arn,
          "${aws_dynamodb_table.user_sessions.arn}/index/*",
          aws_dynamodb_table.magic_link_tokens.arn,
          "${aws_dynamodb_table.magic_link_tokens.arn}/index/*",
          aws_dynamodb_table.audit_logs.arn,
          "${aws_dynamodb_table.audit_logs.arn}/index/*"
        ]
      },
      {
        Sid    = "SecretsManagerAccessForJWT"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.jwt_secret_key.arn
      },
      {
        Sid    = "KMSAccessForSecrets"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.secrets.arn
      },
      {
        Sid    = "SESAccessForEmail"
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = [
          aws_ses_domain_identity.main.arn,
          aws_ses_email_identity.noreply.arn
        ]
      }
    ]
  })
}
