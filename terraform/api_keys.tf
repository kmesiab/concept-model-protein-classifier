# DynamoDB table for API key management
resource "aws_dynamodb_table" "api_keys" {
  name         = "protein-classifier-api-keys"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "api_key_hash"

  attribute {
    name = "api_key_hash"
    type = "S"
  }

  attribute {
    name = "user_email"
    type = "S"
  }

  attribute {
    name = "api_key_id"
    type = "S"
  }

  # Global secondary index to query keys by user email
  global_secondary_index {
    name            = "UserEmailIndex"
    hash_key        = "user_email"
    range_key       = "api_key_id"
    projection_type = "ALL"
  }

  # Global secondary index to query by api_key_id for rotation/revocation
  global_secondary_index {
    name            = "ApiKeyIdIndex"
    hash_key        = "api_key_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.api_keys.arn
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "protein-classifier-api-keys"
    Description = "DynamoDB table for API key storage and management"
  }
}

# DynamoDB table for user sessions (JWT refresh tokens)
resource "aws_dynamodb_table" "user_sessions" {
  name         = "protein-classifier-user-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "user_email"
    type = "S"
  }

  # Global secondary index to query sessions by user email
  global_secondary_index {
    name            = "UserEmailIndex"
    hash_key        = "user_email"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.sessions.arn
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "protein-classifier-user-sessions"
    Description = "DynamoDB table for user session management"
  }
}

# DynamoDB table for magic link tokens (email authentication)
resource "aws_dynamodb_table" "magic_link_tokens" {
  name         = "protein-classifier-magic-link-tokens"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "token"

  attribute {
    name = "token"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.sessions.arn
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "protein-classifier-magic-link-tokens"
    Description = "DynamoDB table for magic link authentication tokens"
  }
}

# DynamoDB table for audit logs
resource "aws_dynamodb_table" "audit_logs" {
  name         = "protein-classifier-audit-logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "event_id"
  range_key    = "timestamp"

  attribute {
    name = "event_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  attribute {
    name = "user_email"
    type = "S"
  }

  # Global secondary index to query logs by user email
  global_secondary_index {
    name            = "UserEmailIndex"
    hash_key        = "user_email"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.audit.arn
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "protein-classifier-audit-logs"
    Description = "DynamoDB table for audit logging of API key operations"
  }
}
