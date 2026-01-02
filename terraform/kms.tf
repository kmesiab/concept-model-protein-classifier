# KMS Key for ALB Logs S3 Bucket Encryption
resource "aws_kms_key" "alb_logs_s3" {
  description             = "KMS key for ALB logs S3 bucket encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name = "alb-logs-s3-encryption-key"
  }
}

# KMS Key Alias for easier identification
resource "aws_kms_alias" "alb_logs_s3" {
  name          = "alias/alb-logs-s3-encryption"
  target_key_id = aws_kms_key.alb_logs_s3.key_id
}

# KMS Key Policy to allow ELB service to encrypt ALB logs in S3
resource "aws_kms_key_policy" "alb_logs_s3" {
  key_id = aws_kms_key.alb_logs_s3.id

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
        Sid    = "AllowELBToUseTheKeyForALBLogs"
        Effect = "Allow"
        Principal = {
          Service = "elasticloadbalancing.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:EncryptionContext:aws:s3:arn" = "arn:aws:s3:::protein-classifier-alb-logs-${var.aws_account_id}/*"
          }
        }
      },
      {
        Sid    = "AllowS3ToUseTheKeyForAccessLogs"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}

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

# KMS Key for DynamoDB Encryption
resource "aws_kms_key" "dynamodb" {
  description             = "KMS key for DynamoDB table encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true
  
  tags = {
    Name = "dynamodb-encryption-key"
  }
}

# KMS Key for ECR Repository Encryption
resource "aws_kms_key" "ecr" {
  description             = "KMS key for ECR repository encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name = "ecr-encryption-key"
  }
}

# KMS Key Policy to allow DynamoDB to use the key
resource "aws_kms_key_policy" "dynamodb" {
  key_id = aws_kms_key.dynamodb.id
}

resource "aws_kms_alias" "ecr" {
  name          = "alias/ecr-encryption"
  target_key_id = aws_kms_key.ecr.key_id
}

# KMS Key Policy to allow ECR to use the key
resource "aws_kms_key_policy" "ecr" {
  key_id = aws_kms_key.ecr.id

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
        Sid    = "Allow DynamoDB to use the key"
        Effect = "Allow"
        Principal = {
          Service = "dynamodb.amazonaws.com"
        Sid    = "Allow ECR to use the key"
        Effect = "Allow"
        Principal = {
          Service = "ecr.amazonaws.com"
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
          StringEquals = {
            "kms:ViaService" = "dynamodb.${var.aws_region}.amazonaws.com"
          }
          StringLike = {
            "kms:EncryptionContext:aws:dynamodb:table-name" = "protein-classifier-*"
            "kms:EncryptionContext:aws:ecr:repositoryArn" = "arn:aws:ecr:${var.aws_region}:${var.aws_account_id}:repository/protein-classifier-api"
          }
        }
      }
    ]
  })
}
