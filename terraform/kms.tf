# KMS Key for CloudWatch Logs Encryption
resource "aws_kms_key" "cloudwatch_logs" {
  description             = "KMS key for CloudWatch log group encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name = "cloudwatch-logs-key"
  }
}

# KMS Key Alias for easier identification
resource "aws_kms_alias" "cloudwatch_logs" {
  name          = "alias/cloudwatch-logs"
  target_key_id = aws_kms_key.cloudwatch_logs.key_id
}

# KMS Key Policy to allow CloudWatch Logs to use the key
resource "aws_kms_key_policy" "cloudwatch_logs" {
  key_id = aws_kms_key.cloudwatch_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs to use the key"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:*"
          }
        }
      }
    ]
  })
}
