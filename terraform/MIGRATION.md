# Terraform Resource Naming Migration Guide

## Overview

This document provides a comprehensive guide for migrating Terraform resources to the new standardized naming convention with the `protein-classifier-` prefix.

## Background

### Problem Statement

Our Terraform resources were not consistently named, making it impossible to identify which application they belong to in a multi-app AWS account. This created several critical issues:

1. **Cannot identify resource ownership** - Resources don't indicate they belong to the protein-classifier app
2. **Risk of accidental modification** - Without clear naming, we might accidentally modify resources from other applications
3. **Cost allocation failure** - Cannot properly track costs per application
4. **Terraform state management complexity** - Difficult to manage when multiple apps share an account
5. **Security audit confusion** - Hard to audit permissions and policies when resource ownership is unclear

### Solution

Implement a standardized naming convention for ALL Terraform resources:

**Pattern:** `protein-classifier-{resource-purpose}-{resource-type}`

**Rules:**
1. Always prefix with `protein-classifier-` for all AWS resources
2. Use hyphens only (no underscores) for AWS resource names
3. Be descriptive about the resource purpose
4. Include resource type when it adds clarity

## Changes Made

### KMS Key Aliases (terraform/kms.tf)

| Old Name | New Name | Resource Type |
|----------|----------|---------------|
| `alias/alb-logs-s3-encryption` | `alias/protein-classifier-alb-logs-kms` | KMS Alias |
| `alias/cloudwatch-logs` | `alias/protein-classifier-cloudwatch-logs-kms` | KMS Alias |
| `alias/dynamodb-encryption` | `alias/protein-classifier-dynamodb-kms` | KMS Alias |
| `alias/ecr-encryption` | `alias/protein-classifier-ecr-kms` | KMS Alias |

**Impact:** KMS aliases will be deleted and recreated with new names during `terraform apply`. The underlying KMS keys remain unchanged and continue to work without interruption. A brief moment during the apply where the alias doesn't exist, but key ARNs remain valid.

### KMS Key Name Tags (terraform/kms.tf)

| Old Tag Value | New Tag Value |
|---------------|---------------|
| `alb-logs-s3-encryption-key` | `protein-classifier-alb-logs-kms` |
| `cloudwatch-logs-key` | `protein-classifier-cloudwatch-logs-kms` |
| `dynamodb-encryption-key` | `protein-classifier-dynamodb-kms` |
| `ecr-encryption-key` | `protein-classifier-ecr-kms` |

**Impact:** Tag updates are in-place changes with no downtime or disruption.

### IAM Inline Policy Names (terraform/iam.tf)

| Old Name | New Name | Parent Role |
|----------|----------|-------------|
| `github-actions-deployment-policy` | `protein-classifier-github-actions-deployment-policy` | `protein-classifier-github-actions-role` |
| `ecs-task-policy` | `protein-classifier-ecs-task-policy` | `protein-classifier-ecs-task-role` |

**Impact:** IAM inline policies will be updated in-place. There may be a brief moment during apply where the old policy is removed and new one added, but the IAM role remains active.

### Lifecycle Protection Added

Added `lifecycle { prevent_destroy = true }` to critical resources:

- All KMS keys (`aws_kms_key.alb_logs_s3`, `aws_kms_key.cloudwatch_logs`, `aws_kms_key.dynamodb`, `aws_kms_key.ecr`)
- DynamoDB table (`aws_dynamodb_table.terraform_locks`)

**Impact:** These resources cannot be accidentally destroyed via `terraform destroy` or resource replacement. Must explicitly remove the lifecycle block to destroy them.

## Migration Process

### Prerequisites

1. **AWS Credentials**: Ensure you have AWS credentials configured with appropriate permissions
2. **Terraform Access**: Access to the Terraform state backend (S3 + DynamoDB)
3. **Backup**: S3 backend has versioning enabled, so state is automatically backed up
4. **Permissions**: Ensure your IAM user/role has permissions to:
   - Read/write KMS key aliases
   - Update IAM policies
   - Update resource tags
   - Access Terraform state in S3 and DynamoDB

### Step-by-Step Migration

#### 1. Review Changes

```bash
cd terraform/
git pull origin main
git checkout <branch-with-naming-changes>
```

Review the changes in:
- `terraform/kms.tf`
- `terraform/iam.tf`
- `terraform/dynamodb.tf`

#### 2. Run Migration Script

The migration script will verify your environment and run `terraform plan`:

```bash
cd terraform/
./migrate-state.sh
```

This script will:
- Verify you're in the correct directory
- Show a summary of changes
- Ask for confirmation
- Initialize Terraform
- Run `terraform plan` to show expected changes

#### 3. Review Terraform Plan

**Expected changes:**

```
Plan: 4 to add, 6 to change, 4 to destroy.
```

**Breakdown:**
- **Add (4)**: New KMS aliases with updated names
- **Change (6)**: 
  - 4 KMS key tags (in-place update)
  - 2 IAM policy names (in-place update)
- **Destroy (4)**: Old KMS aliases (replaced by new ones)

**Critical Verification:**
- ✅ Zero KMS **keys** being destroyed (only aliases)
- ✅ Zero DynamoDB tables being destroyed
- ✅ Zero IAM **roles** being destroyed (only inline policies updated)
- ✅ All changes are in-place updates or alias recreations

**Red Flags (STOP if you see these):**
- ❌ `aws_kms_key.alb_logs_s3` will be destroyed
- ❌ `aws_kms_key.cloudwatch_logs` will be destroyed
- ❌ `aws_kms_key.dynamodb` will be destroyed
- ❌ `aws_kms_key.ecr` will be destroyed
- ❌ `aws_dynamodb_table.terraform_locks` will be destroyed
- ❌ Any IAM role being destroyed

If you see any of these, **DO NOT APPLY**. Something is wrong.

#### 4. Apply Changes

If the plan looks correct:

```bash
terraform apply
```

Review the plan one more time when prompted, then type `yes` to apply.

#### 5. Verify in AWS Console

After applying, verify the changes in AWS Console:

**KMS Keys:**
1. Navigate to: AWS Console → KMS → Customer managed keys
2. Verify aliases are updated:
   - `alias/protein-classifier-alb-logs-kms`
   - `alias/protein-classifier-cloudwatch-logs-kms`
   - `alias/protein-classifier-dynamodb-kms`
   - `alias/protein-classifier-ecr-kms`
3. Verify Name tags are updated in each key's details

**IAM Policies:**
1. Navigate to: AWS Console → IAM → Roles
2. Check `protein-classifier-github-actions-role`
   - Verify policy name is `protein-classifier-github-actions-deployment-policy`
3. Check `protein-classifier-ecs-task-role`
   - Verify policy name is `protein-classifier-ecs-task-policy`

#### 6. Test Application Functionality

After migration, verify that:

1. **GitHub Actions workflows** can still:
   - Push images to ECR
   - Deploy to ECS
   - Access Terraform state in S3/DynamoDB

2. **ECS tasks** can still:
   - Pull images from ECR
   - Write logs to CloudWatch
   - Access any required AWS services

3. **ALB** can still:
   - Write access logs to S3
   - Route traffic to ECS tasks

## Rollback Procedure

If something goes wrong during migration:

### Option 1: Terraform State Rollback (If migration failed)

If `terraform apply` failed partway through:

```bash
# S3 backend has versioning enabled
# Restore previous state version from S3 console or CLI
aws s3api list-object-versions \
  --bucket protein-classifier-terraform-state \
  --prefix protein-classifier/terraform.tfstate

# Download previous version
aws s3api get-object \
  --bucket protein-classifier-terraform-state \
  --key protein-classifier/terraform.tfstate \
  --version-id <previous-version-id> \
  terraform.tfstate.backup

# Push it back as current (requires removing state lock if present)
# Contact DevOps team for assistance with this
```

### Option 2: Git Rollback (If apply succeeded but caused issues)

```bash
# Revert the commit with naming changes
git revert <commit-hash>
git push

# Re-run terraform apply to restore old names
cd terraform/
terraform apply
```

**Note:** This will delete the new aliases and recreate the old ones, and update policy names back. No data loss occurs.

## Troubleshooting

### Issue: "Error acquiring the state lock"

**Cause:** Another Terraform operation is in progress or a previous operation didn't clean up properly.

**Solution:**
```bash
# Check DynamoDB for locks
aws dynamodb get-item \
  --table-name protein-classifier-terraform-locks \
  --key '{"LockID":{"S":"protein-classifier-terraform-state/protein-classifier/terraform.tfstate-md5"}}'

# If stale lock exists (check timestamp), force unlock
terraform force-unlock <lock-id>
```

### Issue: "KMS key policy prevents deletion"

**Cause:** The `prevent_destroy` lifecycle rule is working as intended.

**Solution:** This is by design. KMS keys should not be destroyed. If you truly need to destroy one, temporarily remove the lifecycle block, apply, destroy, then re-add the lifecycle block.

### Issue: "Access Denied" errors during apply

**Cause:** IAM permissions insufficient for the migration.

**Solution:** Ensure your IAM user/role has:
- `kms:CreateAlias`, `kms:DeleteAlias`, `kms:UpdateAlias`
- `iam:PutRolePolicy`, `iam:DeleteRolePolicy`
- `kms:TagResource`, `kms:UntagResource`
- Full access to S3 state bucket and DynamoDB locks table

### Issue: GitHub Actions failing after migration

**Cause 1:** GitHub Actions role policy might need time to propagate.

**Solution:** Wait 1-2 minutes and retry. IAM changes can take up to 60 seconds to propagate.

**Cause 2:** Hard-coded KMS alias references in application code.

**Solution:** Search codebase for old alias names and update:
```bash
grep -r "alb-logs-s3-encryption" .
grep -r "cloudwatch-logs" . | grep -v "protein-classifier-cloudwatch-logs"
grep -r "dynamodb-encryption" .
grep -r "ecr-encryption" .
```

## Testing Checklist

After migration, verify:

- [ ] `terraform plan` shows no changes
- [ ] KMS aliases visible in AWS Console with new names
- [ ] KMS key Name tags updated in AWS Console
- [ ] IAM policy names updated in IAM console
- [ ] GitHub Actions can push to ECR
- [ ] GitHub Actions can deploy to ECS
- [ ] ECS tasks starting successfully
- [ ] ECS tasks writing to CloudWatch Logs
- [ ] ALB writing access logs to S3
- [ ] No errors in CloudWatch Logs for ECS tasks
- [ ] API endpoints responding correctly
- [ ] No cost/billing alerts from unexpected resource recreation

## Success Criteria

After this migration:

- ✅ Every AWS resource created by this Terraform has `protein-classifier-` prefix
- ✅ Resource names use hyphens (not underscores) consistently  
- ✅ Anyone viewing AWS Console can immediately identify protein-classifier resources
- ✅ Cost allocation and security audits are straightforward
- ✅ No risk of confusing resources with other applications in the account
- ✅ Critical resources protected from accidental deletion with lifecycle rules

## Additional Notes

### Why KMS Aliases are Recreated

Terraform treats changes to the `name` attribute of `aws_kms_alias` as requiring replacement. This is safe because:

1. The underlying KMS key is NOT deleted
2. Resources encrypted with the key continue to work
3. References using the key ARN (not alias) are unaffected
4. Only the alias (pointer to the key) is recreated

### Why IAM Policies are Updated In-Place

IAM inline policies are part of the parent role resource. When we change the `name` attribute of `aws_iam_role_policy`, Terraform updates the policy in-place by:

1. Creating a new policy with the new name
2. Deleting the old policy
3. Both happen within the same API transaction, minimizing downtime

### State Locking During Migration

The migration script and Terraform operations use DynamoDB-based state locking to prevent concurrent modifications. If migration is interrupted:

1. Lock will auto-expire after timeout (typically 15 minutes)
2. Or manually unlock with `terraform force-unlock <lock-id>`
3. State versioning in S3 provides rollback capability

## Support

If you encounter issues during migration:

1. **Check Terraform Plan**: Ensure no unexpected resource deletions
2. **Review AWS Console**: Verify resource state matches expectations
3. **Check CloudWatch Logs**: Look for application errors
4. **Contact Team**: Reach out to DevOps team if stuck

## References

- [Issue #XXX](link-to-issue): Original issue requesting standardized naming
- [PR #XXX](link-to-pr): Pull request implementing these changes
- [Terraform State Management](https://developer.hashicorp.com/terraform/language/state)
- [AWS KMS Key Aliases](https://docs.aws.amazon.com/kms/latest/developerguide/kms-alias.html)
- [AWS IAM Policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)
