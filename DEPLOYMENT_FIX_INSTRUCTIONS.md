# Production Deployment Fix - Instructions

## What's Wrong

The production API at https://api.proteinclassifier.com/docs is returning 503 because:

1. ✅ ECR repository `protein-classifier-api` exists
2. ❌ But it contains **0 images** (no `:latest` tag)
3. ❌ ECS service can't start tasks without an image
4. ❌ Docker build workflow fails with KMS permission error

## Root Cause

The ECR repository uses **KMS encryption**, but the GitHub Actions role didn't have permissions to encrypt images when pushing. This caused the Docker build workflow to fail with a misleading "repository does not exist" error (it actually meant "KMS permission denied").

## The Fix (This PR)

**File: `terraform/kms.tf`**

Added two statements to the ECR KMS key policy:

1. **`AllowGitHubActionsToUseECRKey`** - Allows GitHub Actions to encrypt/decrypt images
2. **`AllowECSTaskExecutionRoleToUseECRKey`** - Allows ECS to decrypt images when pulling

## Steps to Restore Production (After Merging This PR)

### 1. Apply Terraform Changes

```bash
# Option A: Via GitHub Actions (Recommended)
# Go to: Actions → "Terraform Apply" → "Run workflow"
# Enter "apply" in the confirmation field
# Click "Run workflow"

# Option B: Via CLI
cd terraform
terraform apply
```

This will update the KMS key policy with the new permissions.

### 2. Build and Push Docker Image

Once Terraform apply completes successfully:

1. Go to **Actions** → **"Build and Push Docker Image"**
2. Click **"Run workflow"** button
3. Select branch: `main`
4. Click **"Run workflow"**

The workflow will:
- ✅ Build Docker image for ARM64 and AMD64
- ✅ Push to ECR with tags `:latest` and `:main-{sha}`
- ✅ Complete in ~2-3 minutes

### 3. Verify ECS Deployment

After the Docker build succeeds:

1. The **"Deploy to ECS"** workflow will automatically trigger
2. Or ECS will automatically detect the new `:latest` image
3. ECS will start tasks with the new image
4. Health checks will pass
5. API will become available

### 4. Verify API is Working

Check the API endpoints:

```bash
# Health check
curl https://api.proteinclassifier.com/health

# API docs
open https://api.proteinclassifier.com/docs
```

You should see:
- ✅ 200 OK response
- ✅ API documentation loads
- ✅ No more 503 errors

## Why This Solution is Simple

- **No workflow coupling**: Terraform only manages infrastructure, Docker build only builds images
- **No automation complexity**: Just fix permissions once, then manually run the build
- **No special ordering required**: After the initial fix, the normal CI/CD flow works automatically
- **Future pushes to `main`** will automatically build and deploy (the existing workflows already handle this)

## What Was Changed

### Before (Broken)

```
GitHub Actions → Push to ECR → ❌ KMS Denied → ECR Error: "repository not found"
```

### After (Fixed)

```
GitHub Actions → Push to ECR → ✅ KMS Allows Encryption → ✅ Image Pushed
ECS → Pull from ECR → ✅ KMS Allows Decryption → ✅ Tasks Start → ✅ API Available
```

## Troubleshooting

### If Docker Build Still Fails

1. Check that Terraform apply completed successfully
2. Verify KMS key policy was updated in AWS Console
3. Check GitHub Actions logs for specific error

### If ECS Tasks Still Fail

1. Check ECS service events in AWS Console
2. View CloudWatch logs: `/ecs/protein-classifier-api`
3. Verify image exists: `aws ecr describe-images --repository-name protein-classifier-api --region us-west-2`

### If API Still Returns 503

1. Check ALB target group health in AWS Console
2. Verify tasks are running: `aws ecs describe-services --cluster protein-classifier-api-1-0-0-prod-cluster --services protein-classifier-api-service`
3. Check task logs in CloudWatch

## Questions?

File an issue or ping @kmesiab
