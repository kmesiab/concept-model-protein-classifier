# Deployment Configuration Guide

This document describes all required and optional environment variables for deploying the Protein Disorder Classification API.

## Required Environment Variables

### Critical - Must Be Set

#### JWT_SECRET_KEY

**CRITICAL**: This key is used to sign JWT tokens and **MUST** be persistent across restarts.

- **Purpose**: Sign and verify JWT access and refresh tokens
- **Requirements**:
  - Minimum 32 characters
  - Cryptographically secure random string
  - **MUST** remain constant across deployments and restarts
  - Changing this will invalidate all existing user sessions
- **Generation**:

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```

- **Storage**: Store in AWS Secrets Manager, AWS Systems Manager Parameter Store, or equivalent secure storage
- **Example**: `JWT_SECRET_KEY=your-very-long-random-secret-key-here`

### DynamoDB Tables

#### DYNAMODB_API_KEYS_TABLE

- **Purpose**: DynamoDB table name for API key storage
- **Default**: `protein-classifier-api-keys`
- **Example**: `DYNAMODB_API_KEYS_TABLE=protein-classifier-api-keys`

#### DYNAMODB_SESSIONS_TABLE

- **Purpose**: DynamoDB table name for user session storage
- **Default**: `protein-classifier-user-sessions`
- **Example**: `DYNAMODB_SESSIONS_TABLE=protein-classifier-user-sessions`

#### DYNAMODB_MAGIC_LINKS_TABLE

- **Purpose**: DynamoDB table name for magic link token storage
- **Default**: `protein-classifier-magic-link-tokens`
- **Example**: `DYNAMODB_MAGIC_LINKS_TABLE=protein-classifier-magic-link-tokens`

#### DYNAMODB_AUDIT_TABLE

- **Purpose**: DynamoDB table name for audit log storage
- **Default**: `protein-classifier-audit-logs`
- **Example**: `DYNAMODB_AUDIT_TABLE=protein-classifier-audit-logs`

### AWS Configuration

#### AWS_REGION

- **Purpose**: AWS region for DynamoDB and other services
- **Default**: `us-west-2`
- **Example**: `AWS_REGION=us-west-2`

### Email Configuration (SMTP)

Required for magic link authentication emails.

#### SMTP_HOST

- **Purpose**: SMTP server hostname
- **Example**: `SMTP_HOST=smtp.gmail.com`

#### SMTP_PORT

- **Purpose**: SMTP server port
- **Default**: `587` (TLS), `465` (SSL)
- **Example**: `SMTP_PORT=587`

#### SMTP_USERNAME

- **Purpose**: SMTP authentication username
- **Example**: `SMTP_USERNAME=api@example.com`

#### SMTP_PASSWORD

- **Purpose**: SMTP authentication password
- **Storage**: Store in secure secrets management
- **Example**: `SMTP_PASSWORD=your-smtp-password`

#### SMTP_FROM_EMAIL

- **Purpose**: Sender email address for magic links
- **Default**: Uses SMTP_USERNAME if not set
- **Example**: `SMTP_FROM_EMAIL=noreply@proteinclassifier.com`

#### BASE_URL

- **Purpose**: Base URL for magic link generation
- **Required**: Production deployments
- **Example**: `BASE_URL=https://api.proteinclassifier.com`

## Optional Environment Variables

### Redis Configuration

#### REDIS_URL

- **Purpose**: Redis connection URL for rate limiting
- **Default**: `redis://localhost:6379/0`
- **Recommended**: Use managed Redis (ElastiCache, Redis Cloud, etc.)
- **Example**: `REDIS_URL=redis://redis.example.com:6379/0`

### CORS Configuration

#### ALLOWED_ORIGINS

- **Purpose**: Comma-separated list of allowed CORS origins
- **Default**: `http://localhost:3000,http://localhost:8000`
- **Example**: `ALLOWED_ORIGINS=https://proteinclassifier.com,https://app.proteinclassifier.com`

### Logging

#### LOG_LEVEL

- **Purpose**: Application logging level
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Example**: `LOG_LEVEL=INFO`

## AWS ECS Task Definition Example

```json
{
  "containerDefinitions": [
    {
      "name": "protein-classifier-api",
      "image": "your-ecr-repo/protein-classifier:latest",
      "environment": [
        {
          "name": "AWS_REGION",
          "value": "us-west-2"
        },
        {
          "name": "DYNAMODB_API_KEYS_TABLE",
          "value": "protein-classifier-api-keys"
        },
        {
          "name": "DYNAMODB_SESSIONS_TABLE",
          "value": "protein-classifier-user-sessions"
        },
        {
          "name": "DYNAMODB_MAGIC_LINKS_TABLE",
          "value": "protein-classifier-magic-link-tokens"
        },
        {
          "name": "DYNAMODB_AUDIT_TABLE",
          "value": "protein-classifier-audit-logs"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://your-elasticache-endpoint:6379/0"
        },
        {
          "name": "BASE_URL",
          "value": "https://api.proteinclassifier.com"
        },
        {
          "name": "SMTP_HOST",
          "value": "smtp.gmail.com"
        },
        {
          "name": "SMTP_PORT",
          "value": "587"
        },
        {
          "name": "ALLOWED_ORIGINS",
          "value": "https://proteinclassifier.com"
        }
      ],
      "secrets": [
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789:secret:jwt-secret-key"
        },
        {
          "name": "SMTP_USERNAME",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789:secret:smtp-username"
        },
        {
          "name": "SMTP_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789:secret:smtp-password"
        }
      ]
    }
  ]
}
```

## Docker Compose Example (Development)

```yaml
version: '3.8'

services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET_KEY=dev-secret-key-change-in-production
      - DYNAMODB_API_KEYS_TABLE=protein-classifier-api-keys
      - DYNAMODB_SESSIONS_TABLE=protein-classifier-user-sessions
      - DYNAMODB_MAGIC_LINKS_TABLE=protein-classifier-magic-link-tokens
      - DYNAMODB_AUDIT_TABLE=protein-classifier-audit-logs
      - AWS_REGION=us-west-2
      - REDIS_URL=redis://redis:6379/0
      - BASE_URL=http://localhost:8000
      - SMTP_HOST=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Security Best Practices

1. **JWT_SECRET_KEY**:
   - NEVER commit to version control
   - Use AWS Secrets Manager or equivalent
   - Rotate every 90 days
   - Use different keys for dev/staging/production

2. **SMTP Credentials**:
   - Store in AWS Secrets Manager
   - Use application-specific passwords when possible
   - Enable 2FA on SMTP account

3. **DynamoDB Access**:
   - Use IAM roles for ECS tasks
   - Follow principle of least privilege
   - Enable encryption at rest (KMS)
   - Enable point-in-time recovery

4. **Redis**:
   - Use encrypted connections (TLS)
   - Restrict network access
   - Enable authentication

## Validation Checklist

Before deploying to production, verify:

- [ ] JWT_SECRET_KEY is set and stored securely
- [ ] All DynamoDB table names are correct
- [ ] AWS region matches your infrastructure
- [ ] SMTP credentials are valid and tested
- [ ] BASE_URL matches your production domain
- [ ] Redis is accessible from application
- [ ] CORS origins include your frontend domains
- [ ] All secrets are in AWS Secrets Manager (not environment variables)
- [ ] IAM roles have necessary DynamoDB permissions
- [ ] Terraform tables are created before deployment

## Troubleshooting

### "Invalid JWT signature"

- JWT_SECRET_KEY changed between deployments
- Multiple instances using different secret keys
- Solution: Ensure JWT_SECRET_KEY is consistent across all instances

### "DynamoDB table not found"

- Table name environment variable mismatch
- Tables not created by Terraform
- Wrong AWS region
- Solution: Verify table names and region, run Terraform apply

### "SMTP authentication failed"

- Invalid SMTP credentials
- App-specific password required but not used
- 2FA blocking access
- Solution: Verify SMTP settings, use app-specific password

### "Rate limiting not working"

- Redis not accessible
- REDIS_URL incorrect
- Network security group blocking access
- Solution: Check Redis connectivity, verify security groups

## Contact

For deployment support, see:

- [AWS Deployment Guide](./AWS_DEPLOYMENT.md)
- [Terraform Configuration](../terraform/README.md)
- [API Documentation](./API.md)
