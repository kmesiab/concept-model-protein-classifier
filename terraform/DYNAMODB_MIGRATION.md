# DynamoDB State Lock Table Migration Guide

This guide explains how to migrate from the old DynamoDB state lock table name
(`prop-insights-terraform-lock`) to the new standardized name
(`protein-classifier-terraform-locks`).

## Problem

After standardizing resource naming to use the `protein-classifier-` prefix
(PR #148), the Terraform backend configuration expects a DynamoDB table named
`protein-classifier-terraform-locks`, but AWS still has the old table named
`prop-insights-terraform-lock`.

This causes Terraform Apply to fail with:

```text
Error: Error acquiring the state lock
ResourceNotFoundException: Requested resource not found
* Unable to retrieve item from DynamoDB table "protein-classifier-terraform-locks"
```

## Solution

Use the automated migration script to handle the transition.

## Automated Migration (Recommended)

The `migrate-dynamodb-table.sh` script automates the entire migration process:

```bash
cd terraform
./migrate-dynamodb-table.sh
```

### What the Script Does

1. **Validates Environment**
   - Checks AWS credentials
   - Verifies you're in the terraform directory
   - Determines current state of both tables

2. **Handles Migration Scenarios**
   - **Old table exists, new doesn't**: Performs full migration
   - **Both tables exist**: Provides cleanup instructions
   - **New table exists, old doesn't**: Confirms migration complete
   - **Neither exists**: Provides bootstrap instructions

3. **Migration Steps** (when old table exists, new doesn't)
   - Creates backup of `backend.tf`
   - Temporarily disables state locking
   - Runs `terraform init` without locking
   - Creates new table via `terraform apply -target=aws_dynamodb_table.terraform_locks`
   - Re-enables state locking
   - Reconfigures backend with `terraform init -reconfigure`
   - Offers to delete old table

## Manual Migration (Alternative)

If you prefer to run the steps manually:

### Step 1: Disable State Locking

Edit `backend.tf` and comment out the `dynamodb_table` line:

```hcl
terraform {
  backend "s3" {
    bucket         = "protein-classifier-terraform-state"
    key            = "protein-classifier/terraform.tfstate"
    region         = "us-west-2"
    # dynamodb_table = "protein-classifier-terraform-locks"  # Temporarily commented
    encrypt        = true
  }
}
```

### Step 2: Initialize Without Locking

```bash
cd terraform
terraform init -reconfigure
```

### Step 3: Create New Table

```bash
terraform apply -target=aws_dynamodb_table.terraform_locks
```

Type `yes` when prompted.

### Step 4: Re-enable State Locking

Uncomment the `dynamodb_table` line in `backend.tf`:

```hcl
dynamodb_table = "protein-classifier-terraform-locks"
```

### Step 5: Reconfigure Backend

```bash
terraform init -reconfigure
```

### Step 6: Verify

```bash
terraform plan
```

Should show no changes for the DynamoDB table.

### Step 7: Clean Up Old Table

After verifying the new table works, delete the old one:

```bash
aws dynamodb delete-table \
  --table-name prop-insights-terraform-lock \
  --region us-west-2
```

## Verification

After migration, verify everything works:

```bash
# Should show no changes
terraform plan

# Verify table exists with correct name
aws dynamodb describe-table \
  --table-name protein-classifier-terraform-locks \
  --region us-west-2

# Verify old table is gone (should fail)
aws dynamodb describe-table \
  --table-name prop-insights-terraform-lock \
  --region us-west-2
```

## For GitHub Actions

The GitHub Actions workflow will automatically work after migration because:

1. The workflow passes backend config via environment variables:

   ```yaml
   env:
     TF_STATE_DYNAMODB_TABLE: ${{ vars.TF_STATE_DYNAMODB_TABLE }}
   ```

2. Update the GitHub repository variable:
   - Go to Settings → Secrets and variables → Actions → Variables
   - Update `TF_STATE_DYNAMODB_TABLE` to `protein-classifier-terraform-locks`

3. The workflow will use the new table name on the next run

## Troubleshooting

### Both Tables Exist

If both tables exist (old and new), this means partial migration or manual
creation. To resolve:

1. Check if new table is in Terraform state:

   ```bash
   terraform state list | grep terraform_locks
   ```

2. If yes, verify it works:

   ```bash
   terraform plan  # Should show no changes for table
   ```

3. Delete old table manually:

   ```bash
   aws dynamodb delete-table \
     --table-name prop-insights-terraform-lock \
     --region us-west-2
   ```

### Neither Table Exists

This is a fresh setup. Follow the bootstrap process in
[terraform/README.md](README.md#bootstrap-process-first-time-setup).

### Migration Script Fails

If the automated script fails:

1. Check the error message carefully
2. Verify AWS credentials are valid
3. Ensure you have permissions to create/delete DynamoDB tables
4. Try the manual migration steps above
5. Check Terraform and AWS CLI versions

### Table Already Imported Error

If you see "Resource already in state", the table is already managed by
Terraform. This is good! Just ensure the name matches:

```bash
terraform state show aws_dynamodb_table.terraform_locks | grep table_name
```

Should show: `table_name = "protein-classifier-terraform-locks"`

## Why DynamoDB Tables Can't Be Renamed

Unlike some AWS resources, DynamoDB tables cannot be renamed directly. The only
way to change a table name is to:

1. Create a new table with the desired name
2. Migrate data (if needed - not required for state locks)
3. Update all references to use the new table
4. Delete the old table

State lock tables rarely contain data (locks are ephemeral), so data migration
is not necessary.

## Related Documentation

- [Terraform README](README.md) - Main infrastructure documentation
- [Backend Configuration](backend.tf) - Terraform state backend config
- [DynamoDB Table Resource](dynamodb.tf) - Table definition

## Support

If you encounter issues during migration:

1. Check this guide's troubleshooting section
2. Review the Terraform logs for specific errors
3. Open an issue in the GitHub repository with:
   - Error messages
   - Current state of both tables (use `aws dynamodb list-tables`)
   - Terraform version and AWS CLI version
