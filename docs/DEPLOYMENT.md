# Deployment Configuration Guide

This document describes all required and optional environment variables for deploying the Protein Disorder Classification API.

## Required Environment Variables

### Critical - Must Be Set

#### JWT_SECRET_NAME

**MANAGED BY AWS SECRETS MANAGER** - This is the recommended and secure approach.

- **Purpose**: Name of the AWS Secrets Manager secret containing the JWT signing key
- **Default**: `protein-classifier-jwt-secret-key`
- **Infrastructure**: Automatically created by Terraform in `terraform/secrets.tf`
- **Features**:
  - Automatic rotation every 90 days
  - KMS encryption at rest
  - Cached for 1 hour to reduce API calls
  - No manual secret management required
- **Example**: `JWT_SECRET_NAME=protein-classifier-jwt-secret-key`

**Important**: The JWT secret key is **NOT** stored as an environment variable. It's fetched from AWS Secrets Manager at runtime and cached. This provides:
- Automatic key rotation support
- Centralized secret management
- Audit trail of secret access
- No secret exposure in environment variables or logs

#### JWT_SECRET_KEY_FALLBACK (Development Only)

- **Purpose**: Fallback JWT secret for local development when Secrets Manager is unavailable
- **WARNING**: **NEVER** use in production
- **Example**: `JWT_SECRET_KEY_FALLBACK=dev-only-insecure-key`

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

### Email Configuration (AWS SES)

Required for magic link authentication emails and API key notifications.

**AWS SES is used in production for reliable, scalable email delivery.**

#### SES_FROM_EMAIL

- **Purpose**: Sender email address for all outbound emails
- **Default**: `noreply@proteinclassifier.com`
- **Requirements**: Must be verified in AWS SES
- **Infrastructure**: Automatically verified by Terraform in `terraform/ses.tf`
- **Example**: `SES_FROM_EMAIL=noreply@proteinclassifier.com`

#### SES_CONFIGURATION_SET

- **Purpose**: AWS SES configuration set name for tracking and monitoring
- **Default**: `protein-classifier-email`
- **Infrastructure**: Automatically created by Terraform in `terraform/ses.tf`
- **Features**:
  - TLS enforcement
  - Reputation metrics tracking
  - Bounce and complaint handling
- **Example**: `SES_CONFIGURATION_SET=protein-classifier-email`

#### USE_SES

- **Purpose**: Enable/disable AWS SES for email delivery
- **Default**: `false` (development mode, emails logged to console)
- **Production**: Automatically enabled when `AWS_EXECUTION_ENV` is set (ECS environment)
- **Example**: `USE_SES=true`

**Note**: In development mode (when AWS SES is not enabled), emails are logged to the console instead of being sent. This allows local testing without AWS credentials.

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
          "name": "JWT_SECRET_NAME",
          "value": "protein-classifier-jwt-secret-key"
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
          "name": "SES_FROM_EMAIL",
          "value": "noreply@proteinclassifier.com"
        },
        {
          "name": "SES_CONFIGURATION_SET",
          "value": "protein-classifier-email"
        },
        {
          "name": "ALLOWED_ORIGINS",
          "value": "https://proteinclassifier.com"
        }
      ]
    }
  ]
}
```

**Note**: JWT secret is **NOT** passed as an environment variable or ECS secret. The application fetches it from AWS Secrets Manager using the IAM role attached to the ECS task. This provides automatic rotation support and better security.

## Docker Compose Example (Development)

```yaml
version: '3.8'

services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET_KEY_FALLBACK=dev-secret-key-not-for-production
      - DYNAMODB_API_KEYS_TABLE=protein-classifier-api-keys
      - DYNAMODB_SESSIONS_TABLE=protein-classifier-user-sessions
      - DYNAMODB_MAGIC_LINKS_TABLE=protein-classifier-magic-link-tokens
      - DYNAMODB_AUDIT_TABLE=protein-classifier-audit-logs
      - AWS_REGION=us-west-2
      - REDIS_URL=redis://redis:6379/0
      - BASE_URL=http://localhost:8000
      # Email disabled in dev (console logging only)
      # Set USE_SES=false or omit to use console logging
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Note**: For local development:
- JWT secret fallback is used when AWS Secrets Manager is unavailable (**never use in production**)
- Emails are logged to console instead of being sent via AWS SES
- DynamoDB can be replaced with local DynamoDB or mocked for testing

## Security Best Practices

1. **JWT Secret Key** (Managed by AWS Secrets Manager):
   - Automatically created by Terraform
   - Encrypted with KMS at rest
   - Supports automatic rotation every 90 days
   - Cached for 1 hour to reduce API calls
   - Never exposed in environment variables or logs
   - Access controlled via IAM policies
   - Audit trail via CloudTrail

2. **AWS SES Email Delivery**:
   - Domain identity automatically verified by Terraform
   - DKIM signing for email authentication
   - Custom MAIL FROM domain for improved deliverability
   - TLS encryption enforced
   - Reputation metrics and bounce tracking enabled
   - No SMTP credentials needed (uses IAM roles)

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

- [ ] JWT secret created in AWS Secrets Manager by Terraform
- [ ] ECS task role has permissions to read JWT secret
- [ ] All DynamoDB table names are correct
- [ ] AWS region matches your infrastructure
- [ ] AWS SES domain identity verified (done by Terraform)
- [ ] AWS SES DKIM records configured in Route53 (done by Terraform)
- [ ] AWS SES moved out of sandbox mode (submit production access request to AWS)
- [ ] BASE_URL matches your production domain
- [ ] Redis is accessible from application
- [ ] CORS origins include your frontend domains
- [ ] IAM roles have necessary permissions (DynamoDB, Secrets Manager, KMS, SES)
- [ ] Terraform resources are created before deployment

## Troubleshooting

### "Failed to fetch JWT secret from AWS Secrets Manager"

- JWT secret not created in Secrets Manager
- IAM role lacks permissions to read secret
- KMS key permissions not granted to ECS task role
- Wrong AWS region configuration
- Solution: Run Terraform to create secret, verify IAM permissions

### "Invalid JWT signature"

- JWT secret was rotated but application cache not refreshed (wait 1 hour or restart)
- Multiple instances using different secrets (should not happen with Secrets Manager)
- Solution: Restart application to refresh cache, verify secret ARN

### "Access denied to JWT secret"

- ECS task role missing `secretsmanager:GetSecretValue` permission
- KMS key policy doesn't allow ECS task role to decrypt
- Solution: Verify IAM policy in terraform/iam.tf includes Secrets Manager and KMS permissions

### "DynamoDB table not found"

- Table name environment variable mismatch
- Tables not created by Terraform
- Wrong AWS region
- Solution: Verify table names and region, run Terraform apply

### "Failed to send email via SES"

- SES domain identity not verified
- SES still in sandbox mode (can only send to verified email addresses)
- IAM role missing `ses:SendEmail` permission
- FROM email address not verified in SES
- Solution: Verify SES domain identity, request production access, check IAM permissions

### "Email MessageRejected: Email address is not verified"

- SES is in sandbox mode (development/testing)
- Recipient email not verified in SES console
- Solution: Request production access from AWS Support to send to any email address

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
