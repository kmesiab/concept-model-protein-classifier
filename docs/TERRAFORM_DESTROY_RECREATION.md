# Terraform Destroy and Recreation Guide

This document explains the destroy/recreation process for the Protein Classifier infrastructure, including all chicken-and-egg scenarios and their solutions.

## Table of Contents

- [Overview](#overview)
- [Chicken-and-Egg Scenarios](#chicken-and-egg-scenarios)
- [Destroy Options](#destroy-options)
- [Recreation Process](#recreation-process)
- [Troubleshooting](#troubleshooting)

## Overview

The infrastructure has **two types of resources**:

### Bootstrap Resources (Outside Terraform)

These resources are **manually provisioned** and are **never destroyed** by Terraform:

1. **S3 State Bucket**: `protein-classifier-terraform-state`
   - Stores Terraform state
   - **Required for Terraform to operate**
   - Manually created before first Terraform run

2. **GitHub OIDC Provider**: `arn:aws:iam::462498369025:oidc-provider/token.actions.githubusercontent.com`
   - Enables GitHub Actions to authenticate to AWS
   - **Required for GitHub Actions workflows to run**
   - Shared across multiple projects

3. **GitHub Actions IAM Role**: `github-actions-terraform`
   - Used by GitHub Actions to run Terraform
   - **Required for workflows to access AWS**
   - Referenced as `data` source in Terraform (not managed)

4. **Route 53 Hosted Zone**: `proteinclassifier.com`
   - DNS delegation for the domain
   - Manually configured with nameservers

### Managed Resources with Lifecycle Protection

These resources **are managed by Terraform** but have `prevent_destroy` lifecycle rules:

1. **DynamoDB State Lock Table**: `protein-classifier-terraform-locks`
   - Prevents concurrent Terraform operations
   - **Required for Terraform state locking**
   - Encrypted with KMS

2. **KMS Keys** (6 total):
   - `protein-classifier-cloudwatch-logs-kms` - CloudWatch log encryption
   - `protein-classifier-dynamodb-kms` - DynamoDB encryption (including state lock)
   - `protein-classifier-ecr-kms` - ECR Docker image encryption
   - `protein-classifier-api-keys-kms` - API keys encryption
   - `protein-classifier-sessions-kms` - User sessions encryption
   - `protein-classifier-audit-kms` - Audit logs encryption
   - `protein-classifier-secrets-kms` - Secrets Manager encryption
   - **All have 10-30 day deletion windows**
   - **Required for encrypted resource access**

3. **Secrets Manager Secrets**:
   - JWT signing keys
   - 30-day deletion window

## Chicken-and-Egg Scenarios

### Scenario 1: DynamoDB State Lock Table

**Problem**: The DynamoDB table is used for Terraform state locking, but it's defined IN the Terraform configuration.

**Solution**:

- **On First Creation**: Bootstrap process (see [terraform/README.md](../terraform/README.md#bootstrap-process-first-time-setup))
  1. Temporarily disable state locking in `backend.tf`
  2. Create the DynamoDB table with `terraform apply -target=aws_dynamodb_table.terraform_locks`
  3. Re-enable state locking
  4. Run `terraform init -reconfigure`

- **After Destroy**:
  - **Partial Destroy** (default): Table is preserved, no bootstrap needed
  - **Full Destroy**: Must repeat bootstrap process

### Scenario 2: KMS Key Permissions

**Problem**: GitHub Actions needs KMS decrypt permissions to access the DynamoDB state lock, but the permissions are defined in Terraform.

**Solution**:

- **On First Creation**: KMS bootstrap process (see [docs/KMS_BOOTSTRAP.md](KMS_BOOTSTRAP.md))
  - Manually grant KMS permissions to GitHub Actions role via AWS CLI or Console
  - Only needed once

- **After Destroy**:
  - **Partial Destroy** (default): KMS keys preserved, no bootstrap needed
  - **Full Destroy with KMS deletion**: Must repeat KMS bootstrap OR wait for deletion period

### Scenario 3: KMS Key Aliases

**Problem**: KMS key aliases cannot be reused until the key completes its deletion period (10-30 days).

**Solution**:

- **Option 1**: Wait for deletion period to complete
- **Option 2**: Cancel scheduled deletion in AWS Console
- **Option 3**: Use different aliases:

  ```hcl
  # Change in terraform/kms.tf
  resource "aws_kms_alias" "dynamodb" {
    name          = "alias/protein-classifier-dynamodb-kms-v2"  # Add version suffix
    target_key_id = aws_kms_key.dynamodb.key_id
  }
  ```

### Scenario 4: GitHub Actions Role

**Problem**: The GitHub Actions IAM role is required to run the destroy workflow, but it's referenced in Terraform.

**Solution**:

- Role is a `data` source (not managed by Terraform)
- It will never be destroyed by Terraform
- **Unsolvable if role is manually deleted**: Must recreate role manually before running any workflows

### Scenario 5: State File Location

**Problem**: After complete destroy, the state file still exists in S3 but contains no resources.

**Solution**:

- **Normal Case**: State file is preserved, subsequent `terraform apply` works
- **Clean Slate**: Manually delete state file from S3 (not recommended)
- **Best Practice**: Leave state file intact - it tracks deletion

## Destroy Options

### Option 1: Partial Destroy (Default - Recommended)

**When to use**: Regular cleanup while preserving ability to quickly recreate

```yaml
Inputs:
  confirm: "destroy"
  remove_lifecycle_protections: false
```

**What gets destroyed**:

- ✅ ECS cluster and services
- ✅ Application Load Balancer
- ✅ VPC and networking
- ✅ ECR repositories
- ✅ CloudWatch log groups
- ✅ Route 53 DNS records (A records, not the hosted zone)
- ✅ S3 buckets (ALB logs)
- ✅ ECS IAM roles

**What is preserved**:

- 🛡️ DynamoDB state lock table
- 🛡️ All KMS keys
- 🛡️ Secrets Manager secrets
- 📦 S3 state bucket (bootstrap resource)
- 🔐 GitHub Actions IAM role (bootstrap resource)
- 🌐 GitHub OIDC provider (bootstrap resource)
- 🌍 Route 53 hosted zone (bootstrap resource)

**Recreation process**:

1. Run Terraform Apply workflow
2. No bootstrap needed
3. Infrastructure recreated in ~10-15 minutes

### Option 2: Full Destroy (Complete Teardown)

**When to use**: Permanent shutdown or changing regions

```yaml
Inputs:
  confirm: "destroy"
  remove_lifecycle_protections: true
```

**What gets destroyed**:

- ✅ Everything from Option 1
- ✅ DynamoDB state lock table
- ✅ All KMS keys (scheduled for deletion)
- ✅ Secrets Manager secrets (scheduled for deletion)

**What is preserved**:

- 📦 S3 state bucket (bootstrap resource)
- 🔐 GitHub Actions IAM role (bootstrap resource)
- 🌐 GitHub OIDC provider (bootstrap resource)
- 🌍 Route 53 hosted zone (bootstrap resource)

**Recreation process**:

1. **Wait**: KMS keys have 10-30 day deletion period
2. **OR Cancel Deletion**: In AWS Console, cancel scheduled deletion for all KMS keys
3. **OR Use New Aliases**: Update `terraform/kms.tf` with new alias names
4. **Then**:
   - Follow [bootstrap process](../terraform/README.md#bootstrap-process-first-time-setup)
   - Follow [KMS bootstrap](KMS_BOOTSTRAP.md)
   - Run Terraform Apply workflow
   - Infrastructure recreated in ~20-30 minutes

## Recreation Process

### After Partial Destroy (Recommended Path)

This is the **happy path** - fastest and simplest recreation:

1. ✅ Run Terraform Apply workflow
2. ✅ Type "apply" to confirm
3. ✅ Wait 10-15 minutes
4. ✅ Infrastructure is back online

**Why this works**:

- State lock table exists
- KMS keys exist with correct permissions
- State file tracks previous resources
- No bootstrap needed

### After Full Destroy (Complete Teardown)

This requires addressing chicken-and-egg scenarios:

#### Path A: Wait for KMS Deletion (Cleanest)

1. **Wait 10-30 days** for KMS keys to be deleted
2. Follow [DynamoDB bootstrap](../terraform/README.md#bootstrap-process-first-time-setup):
   - Comment out `dynamodb_table` in `backend.tf`
   - `terraform init`
   - `terraform apply -target=aws_dynamodb_table.terraform_locks`
   - Uncomment `dynamodb_table`
   - `terraform init -reconfigure`
3. `terraform apply` to create remaining resources
4. Follow [KMS bootstrap](KMS_BOOTSTRAP.md) to grant GitHub Actions KMS permissions
5. Run Terraform Apply workflow

#### Path B: Cancel KMS Deletion (Faster)

1. **AWS Console** → **KMS** → **Customer managed keys**
2. For each key with "Pending deletion":
   - Click on the key
   - Click **"Cancel key deletion"**
3. Run Terraform Apply workflow
4. Infrastructure recreated (no bootstrap needed)

#### Path C: Use New KMS Aliases (Alternative)

1. Update `terraform/kms.tf`:

   ```hcl
   resource "aws_kms_alias" "dynamodb" {
     name          = "alias/protein-classifier-dynamodb-kms-v2"
     target_key_id = aws_kms_key.dynamodb.key_id
   }
   # Repeat for all 6 KMS aliases
   ```

2. Follow [DynamoDB bootstrap](../terraform/README.md#bootstrap-process-first-time-setup)
3. `terraform apply`
4. Follow [KMS bootstrap](KMS_BOOTSTRAP.md)
5. Run Terraform Apply workflow

## Troubleshooting

### "DynamoDB table does not exist" during init

**Cause**: Full destroy removed the state lock table

**Solution**: Follow [DynamoDB bootstrap process](../terraform/README.md#bootstrap-process-first-time-setup)

### "KMS key access denied" during init

**Cause**: Full destroy removed KMS keys or permissions

**Solution**:

1. Check if keys exist in AWS Console
2. If keys exist: Follow [KMS bootstrap](KMS_BOOTSTRAP.md)
3. If keys don't exist: Follow full recreation process

### "Alias already exists" during apply

**Cause**: KMS keys are scheduled for deletion but aliases still exist

**Solution**:

- **Option 1**: Cancel key deletion in AWS Console
- **Option 2**: Wait for deletion period
- **Option 3**: Use new alias names (see Path C above)

### "Cannot assume role" during workflow

**Cause**: GitHub Actions IAM role was manually deleted

**Solution**: Recreate the role manually (outside Terraform scope)

### State file is empty but resources exist in AWS

**Cause**: State file was manually deleted or corrupted

**Solution**:

1. **Option 1**: Import existing resources:

   ```bash
   cd terraform
   terraform import aws_dynamodb_table.terraform_locks protein-classifier-terraform-locks
   # Repeat for all resources
   ```

2. **Option 2**: Manually delete resources in AWS Console, start fresh

## Best Practices

1. **Default to Partial Destroy**: Use `remove_lifecycle_protections: false` unless permanently shutting down
2. **Keep Bootstrap Resources**: Never manually delete S3 state bucket, OIDC provider, or GitHub Actions role
3. **Test Recreation**: After partial destroy, test recreation process in non-prod environment
4. **Document Changes**: If using custom KMS aliases, document in team wiki
5. **State File Backups**: S3 state bucket has versioning enabled - you can restore previous states

## Summary Matrix

| Scenario | Partial Destroy | Full Destroy | Manual Deletion |
|----------|----------------|--------------|-----------------|
| **State Lock Table** | ✅ Preserved | ❌ Destroyed | ⚠️ Bootstrap required |
| **KMS Keys** | ✅ Preserved | ❌ Deletion scheduled | ⚠️ Bootstrap required |
| **Secrets** | ✅ Preserved | ❌ Deletion scheduled | ⚠️ Manual recreation |
| **S3 State Bucket** | ✅ Preserved | ✅ Preserved | ❌ **NEVER DELETE** |
| **GitHub Actions Role** | ✅ Preserved | ✅ Preserved | ❌ **NEVER DELETE** |
| **OIDC Provider** | ✅ Preserved | ✅ Preserved | ❌ **NEVER DELETE** |
| **Recreation Time** | ~10-15 min | ~20-30 min + wait | Varies |
| **Bootstrap Required** | ❌ No | ✅ Yes | ✅ Yes |

## Related Documentation

- [Terraform README](../terraform/README.md) - Main Terraform documentation
- [KMS Bootstrap Guide](KMS_BOOTSTRAP.md) - KMS permissions bootstrap
- [Terraform Validation](TERRAFORM_VALIDATION.md) - CI/CD pipeline
- [GitHub Actions Workflows](../.github/workflows/README.md) - Workflow documentation
