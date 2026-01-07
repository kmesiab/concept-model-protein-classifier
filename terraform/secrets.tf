# AWS Secrets Manager for JWT Secret Key
# Supports automatic rotation and centralized secret management

# KMS key for encrypting secrets
resource "aws_kms_key" "secrets" {
  description             = "KMS key for encrypting Secrets Manager secrets"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "protein-classifier-secrets-kms"
    Description = "Encryption key for Secrets Manager"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/protein-classifier-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# Generate cryptographically secure random secret (64 bytes = 512 bits)
resource "random_password" "jwt_secret" {
  length  = 64
  special = true

  lifecycle {
    ignore_changes = [result]
  }
}

# JWT Secret Key for signing access and refresh tokens
resource "aws_secretsmanager_secret" "jwt_secret_key" {
  name        = "protein-classifier-jwt-secret-key"
  description = "JWT secret key for signing authentication tokens"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = {
    Name        = "protein-classifier-jwt-secret-key"
    Description = "JWT signing key"
    Environment = var.environment
  }
}

# Generate initial secret value
resource "aws_secretsmanager_secret_version" "jwt_secret_key_initial" {
  secret_id = aws_secretsmanager_secret.jwt_secret_key.id
  secret_string = jsonencode({
    key       = random_password.jwt_secret.result
    algorithm = "HS256"
  })
}

