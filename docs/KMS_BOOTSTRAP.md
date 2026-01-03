# KMS Permissions Bootstrap Guide

## Problem Statement

We have a **chicken-and-egg problem** that prevents Terraform Apply from running:

1. ✅ **PR #132 merged** - KMS permissions added to Terraform code
2. ❌ **Terraform Apply fails** - Can't access DynamoDB state lock table
3. 🔄 **Root cause** - The KMS policy changes are IN the code but haven't been applied to AWS yet
4. 🔒 **Deadlock** - Terraform can't run to apply those changes because it needs those permissions to access the DynamoDB state lock!

### The Error

```text
table "protein-classifier-terraform-locks": operation error DynamoDB: GetItem
KMS key access denied error:
User: arn:aws:sts::462498369025:assumed-role/github-actions-terraform/GitHubActions
is not authorized to perform: kms:Decrypt on resource:
arn:aws:kms:us-west-2:462498369025:key/e9b37450-f4df-45d6-a336-aefd3b1d0896
because no identity-based policy allows the kms:Decrypt action
```

## Solutions

We provide **three approaches** to solve this problem:

### Option 1: GitHub Actions Workflow (Recommended)

This is the **easiest and safest** approach. A one-time GitHub Actions workflow will update the KMS key policy automatically.

**Prerequisites:**

- Access to GitHub Actions in this repository
- AWS role with permission to modify KMS key policies (e.g., `github-actions-terraform-admin`)

**Steps:**

1. Go to **Actions** tab in GitHub
2. Select **Bootstrap KMS Permissions** workflow
3. Click **Run workflow**
4. Type `bootstrap` to confirm
5. Wait for workflow to complete
6. Run the regular **Terraform Apply** workflow

**What it does:**

- Validates AWS credentials
- Retrieves current KMS key policy
- Adds GitHub Actions role permissions
- Verifies the update was successful

### Option 2: Bash Script (Local Execution)

Run the bootstrap script locally with AWS CLI credentials.

**Prerequisites:**

- AWS CLI installed and configured
- `jq` installed (`sudo apt-get install jq` or `brew install jq`)
- AWS credentials with permission to modify KMS key policies

**Steps:**

```bash
cd terraform
./bootstrap-kms-permissions.sh
```

**With custom parameters:**

```bash
./bootstrap-kms-permissions.sh \
  e9b37450-f4df-45d6-a336-aefd3b1d0896 \
  arn:aws:iam::462498369025:role/github-actions-terraform
```

**Using environment variables:**

```bash
export KMS_KEY_ID=e9b37450-f4df-45d6-a336-aefd3b1d0896
export GITHUB_ACTIONS_ROLE_ARN=arn:aws:iam::462498369025:role/github-actions-terraform
export AWS_REGION=us-west-2
./bootstrap-kms-permissions.sh
```

### Option 3: Python Script (Local Execution)

Use the Python script if you prefer boto3 over AWS CLI.

**Prerequisites:**

- Python 3.7+
- boto3 installed (`pip install boto3`)
- AWS credentials with permission to modify KMS key policies

**Steps:**

```bash
cd terraform
python3 bootstrap_kms_permissions.py
```

**With custom parameters:**

```bash
python3 bootstrap_kms_permissions.py \
  --key-id e9b37450-f4df-45d6-a336-aefd3b1d0896 \
  --role-arn arn:aws:iam::462498369025:role/github-actions-terraform \
  --region us-west-2
```

**Using environment variables:**

```bash
export KMS_KEY_ID=e9b37450-f4df-45d6-a336-aefd3b1d0896
export GITHUB_ACTIONS_ROLE_ARN=arn:aws:iam::462498369025:role/github-actions-terraform
python3 bootstrap_kms_permissions.py
```

### Option 4: Manual AWS CLI Command

If you can't use the scripts, run this AWS CLI command directly:

**Step 1: Get current policy**

```bash
aws kms get-key-policy \
  --key-id e9b37450-f4df-45d6-a336-aefd3b1d0896 \
  --policy-name default \
  --region us-west-2 \
  --query 'Policy' \
  --output text > current-policy.json
```

**Step 2: Edit the policy**

Add this statement to the `Statement` array in `current-policy.json`:

```json
{
  "Sid": "AllowGitHubActionsToUseDynamoDBKey",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::462498369025:role/github-actions-terraform"
  },
  "Action": [
    "kms:Decrypt",
    "kms:DescribeKey",
    "kms:GenerateDataKey",
    "kms:Encrypt"
  ],
  "Resource": "*"
}
```

**Step 3: Apply the updated policy**

```bash
aws kms put-key-policy \
  --key-id e9b37450-f4df-45d6-a336-aefd3b1d0896 \
  --policy-name default \
  --policy file://current-policy.json \
  --region us-west-2
```

### Option 5: AWS Console (Manual)

If you prefer using the AWS Console:

1. Go to **AWS Console** → **KMS** → **Customer managed keys**
2. Search for key ID: `e9b37450-f4df-45d6-a336-aefd3b1d0896`
3. Click on the key
4. Go to **Key policy** tab
5. Click **Edit**
6. Add the statement from Option 4 Step 2 to the policy
7. Click **Save changes**

## What Permissions Are Granted?

The bootstrap process grants the GitHub Actions role (`arn:aws:iam::462498369025:role/github-actions-terraform`) the following KMS permissions:

- **`kms:Decrypt`** - Required to decrypt DynamoDB state lock items
- **`kms:DescribeKey`** - Required to get key metadata
- **`kms:GenerateDataKey`** - Required to generate data encryption keys
- **`kms:Encrypt`** - Required to encrypt DynamoDB state lock items

These permissions allow Terraform to:

- Read the state lock from DynamoDB
- Write state locks to DynamoDB
- Access the Terraform state file (if encrypted with the same key)

## Verification

After running the bootstrap, verify the permissions were applied:

```bash
aws kms get-key-policy \
  --key-id e9b37450-f4df-45d6-a336-aefd3b1d0896 \
  --policy-name default \
  --region us-west-2 \
  --query 'Policy' \
  --output text | jq '.Statement[] | select(.Sid == "AllowGitHubActionsToUseDynamoDBKey")'
```

You should see the statement with the GitHub Actions role and the four KMS actions.

## Testing Terraform Apply

After bootstrap completes:

1. Go to **Actions** → **Terraform Apply**
2. Click **Run workflow**
3. Type `apply` to confirm
4. The workflow should now complete successfully!

## Troubleshooting

### "AWS credentials are not configured"

**Problem:** AWS CLI or boto3 can't find credentials.

**Solution:**

```bash
aws configure
# OR export credentials
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_SESSION_TOKEN=your-session-token  # if using temporary credentials
```

### "KMS key not found"

**Problem:** The KMS key ID is incorrect or doesn't exist in the specified region.

**Solution:**

- Verify the KMS key ID: `e9b37450-f4df-45d6-a336-aefd3b1d0896`
- Verify the region: `us-west-2`
- Check if the key exists in AWS Console

### "Access Denied" when updating policy

**Problem:** Your AWS credentials don't have permission to modify KMS key policies.

**Solution:**

- Ensure you're using an admin or KMS admin role
- Check your IAM permissions include `kms:PutKeyPolicy`
- Try using a different set of credentials with broader permissions

### Script shows "already has permissions" but Terraform still fails

**Problem:** The permissions might be correct but there's another issue.

**Solution:**

1. Check the exact error message in Terraform logs
2. Verify the role ARN matches exactly (no typos)
3. Check if there are any Deny statements in the policy
4. Try running Terraform with `-debug` flag for more details

## One-Time Operation

**Important:** This bootstrap only needs to be run **once**. After the initial bootstrap:

1. ✅ Terraform Apply will work
2. ✅ Future Terraform updates will manage the KMS policy
3. ✅ No need to run bootstrap again

The KMS permissions are now defined in `terraform/kms.tf`, so future changes will be managed by Terraform.

## Related Documentation

- [Terraform README](terraform/README.md) - Main Terraform documentation
- [GitHub Actions Workflows](.github/workflows/README.md) - Workflow documentation
- [AWS KMS Key Policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html) - AWS documentation

## Support

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/kmesiab/concept-model-protein-classifier/issues)
2. Open a new issue with:
   - The option you tried
   - The complete error message
   - Your AWS region and account ID
   - Sanitized version of the error (remove sensitive info)
