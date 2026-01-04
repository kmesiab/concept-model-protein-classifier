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
        # Root account has full admin permissions for key management
        # Required for key administration by account owner/repository maintainers
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        # ELB service requires comprehensive permissions for ALB log delivery to KMS-encrypted S3
        # Includes CreateGrant for S3 server-side encryption operations
        # Scoped to ELB service via ViaService condition for security
        Sid    = "AllowELBToUseTheKeyForALBLogs"
        Effect = "Allow"
        Principal = {
          Service = "elasticloadbalancing.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "elasticloadbalancing.${var.aws_region}.amazonaws.com"
          }
        }
      },
      {
        # Regional ELB service account requires KMS permissions to encrypt logs
        # This matches the S3 bucket policy which grants write access to this account
        # Without this, the ELB service account can write to S3 but cannot encrypt the objects
        # Includes CreateGrant for S3 server-side encryption operations
        Sid    = "AllowRegionalELBAccountToUseTheKey"
        Effect = "Allow"
        Principal = {
          AWS = data.aws_elb_service_account.main.arn
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        # S3 service needs comprehensive permissions for server-side encryption
        # - Encrypt/Decrypt: Basic encryption operations
        # - GenerateDataKey: Envelope encryption for new objects
        # - CreateGrant: Required for S3 bucket keys (bucket_key_enabled = true)
        # - ReEncrypt: Required for lifecycle transitions (GLACIER, INTELLIGENT_TIERING)
        # - DescribeKey: Metadata operations
        Sid    = "AllowS3ToUseTheKeyForServerSideEncryption"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
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
            "kms:ViaService" = "s3.${var.aws_region}.amazonaws.com"
          }
        }
      },
      {
        # S3 Logging service is separate from general S3 service
        # Requires same comprehensive permissions for encrypting access logs
        # This matches the S3 bucket policy which grants write access to this service
        Sid    = "AllowS3LoggingToUseTheKeyForAccessLogs"
        Effect = "Allow"
        Principal = {
          Service = "logging.s3.amazonaws.com"
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
            "kms:ViaService" = "s3.${var.aws_region}.amazonaws.com"
          }
        }
      },
      {
        # GitHub Actions needs decrypt/describe/generate for Terraform state access
        # Required for Terraform operations that read/write to encrypted S3 backend
        Sid    = "AllowGitHubActionsToManageKey"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.github_actions.arn
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:GenerateDataKey"
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

# KMS Key Alias for DynamoDB encryption
resource "aws_kms_alias" "dynamodb" {
  name          = "alias/dynamodb-encryption"
  target_key_id = aws_kms_key.dynamodb.key_id
}

# KMS Key Policy for DynamoDB encryption
resource "aws_kms_key_policy" "dynamodb" {
  key_id = aws_kms_key.dynamodb.id

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
          }
        }
      },
      {
        # GitHub Actions principal statement intentionally omits encryption context condition.
        # IAM principals accessing DynamoDB directly for state locking don't provide the same
        # encryption context that DynamoDB service operations use. The encryption context
        # condition on the service principal above ensures server-side encryption, while
        # this statement allows GitHub Actions client-side access to the encrypted table.
        Sid    = "AllowGitHubActionsToUseDynamoDBKey"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.github_actions.arn
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
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

# KMS Key Alias for ECR encryption
resource "aws_kms_alias" "ecr" {
  name          = "alias/ecr-encryption"
  target_key_id = aws_kms_key.ecr.key_id
}

# KMS Key Policy for ECR encryption
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
            "kms:EncryptionContext:aws:ecr:repositoryArn" = "arn:aws:ecr:${var.aws_region}:${var.aws_account_id}:repository/protein-classifier-api"
          }
        }
      }
    ]
  })
}
