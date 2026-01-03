# Terraform Infrastructure for Protein Classifier API

This directory contains the Terraform infrastructure code for deploying the Protein Classifier API to AWS ECS Fargate with OIDC authentication.

## 🚀 Triple-Gated Validation Pipeline

All infrastructure changes are automatically validated through our **Triple-Gated CI/CD Pipeline**:

1. 🔍 **Gate 1: TFLint** - Catch provider-specific errors and enforce naming conventions
2. 🔒 **Gate 2: Security Scanner** - Scan for security issues (Trivy)
3. 💰 **Gate 3: Infracost** - Show cost estimates before applying

**[View Pipeline Documentation →](../docs/TERRAFORM_VALIDATION.md)**

This acts as an automated Senior DevOps Reviewer for all Terraform changes.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured (for initial setup only)
- Access to AWS account `462498369025`

## Infrastructure Components

### Already Provisioned

- **Domain**: `proteinclassifier.com` (delegated to Route 53)
- **Route 53 Hosted Zone**: Created with nameservers
- **S3 Terraform State Bucket**: `protein-classifier-terraform-state` (us-west-2)
- **GitHub OIDC Provider**: `arn:aws:iam::462498369025:oidc-provider/token.actions.githubusercontent.com`

### Managed by Terraform

- **DynamoDB State Lock Table**: `protein-classifier-terraform-locks`
- **IAM Role**: GitHub Actions OIDC role with deployment permissions
- **VPC**: Custom VPC with public and private subnets across 2 AZs
- **NAT Gateways**: For private subnet internet access
- **VPC Flow Logs**: CloudWatch log group and flow log for network monitoring
- **ECR Repository**: `protein-classifier-api` for Docker images
- **ECS Cluster**: `protein-classifier-api-1-0-0-prod-cluster`
- **ECS Service**: Fargate service running on port 8000
- **Application Load Balancer**: HTTPS (443) → ECS (8000)
- **S3 Bucket**: ALB access logs with lifecycle policies (Intelligent-Tiering, Glacier archival)
- **ACM Certificate**: SSL certificate for `api.proteinclassifier.com`
- **Route 53 DNS**: A record pointing to ALB
- **CloudWatch Logs**: Log group for ECS container logs

## File Structure

```text
terraform/
├── backend.tf           # S3 backend configuration
├── provider.tf          # AWS provider configuration
├── variables.tf         # Input variables
├── dynamodb.tf          # DynamoDB state lock table
├── iam.tf              # IAM roles for GitHub Actions and ECS
├── ecr.tf              # ECR repository for Docker images
├── vpc.tf              # VPC, subnets, NAT gateways, security groups
├── alb.tf              # Application Load Balancer and target groups
├── acm.tf              # ACM certificate and DNS validation
├── ecs.tf              # ECS cluster, task definition, and service
├── route53.tf          # DNS A record for API endpoint
└── outputs.tf          # Output values
```

## Deployment Instructions

### Bootstrap Process (First-Time Setup)

**Note**: There's a chicken-and-egg problem with the DynamoDB state lock table. The backend configuration references the DynamoDB table before it exists. Follow these steps for initial setup:

1. **Temporarily disable state locking**:

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

2. **Initialize Terraform**:

   ```bash
   cd terraform
   terraform init
   ```

3. **Create the DynamoDB table**:

   ```bash
   terraform apply -target=aws_dynamodb_table.terraform_locks
   ```

4. **Re-enable state locking**:

   Uncomment the `dynamodb_table` line in `backend.tf`:

   ```hcl
   dynamodb_table = "protein-classifier-terraform-locks"
   ```

5. **Reconfigure the backend**:

   ```bash
   terraform init -reconfigure
   ```

### Regular Deployment

After the initial bootstrap, follow these steps:

1. **Review the plan**:

   ```bash
   terraform plan
   ```

2. **Apply the infrastructure**:

   ```bash
   terraform apply
   ```

   Type `yes` when prompted to confirm.

### Outputs

After applying, Terraform will output important information:

```text
ecr_repository_url        = URL of the ECR repository
ecs_cluster_name          = Name of the ECS cluster
ecs_service_name          = Name of the ECS service
alb_dns_name             = DNS name of the ALB
api_url                  = https://api.proteinclassifier.com
github_actions_role_arn  = ARN of the GitHub Actions IAM role
cloudwatch_log_group     = CloudWatch log group name
```

## GitHub Actions Workflows

Two workflows are configured in `.github/workflows/`:

### 1. Docker Build (`docker-build.yml`)

- **Trigger**: Push to `main` branch (api directory changes)
- **Authentication**: OIDC (no AWS secrets required)
- **Actions**:
  - Builds Docker image from `api/Dockerfile`
  - Pushes to ECR repository
  - Tags: latest, branch name, commit SHA

### 2. ECS Deploy (`deploy-ecs.yml`)

- **Trigger**: After successful Docker build
- **Authentication**: OIDC (no AWS secrets required)
- **Actions**:
  - Updates ECS task definition with new image
  - Deploys to ECS service
  - Waits for service stability

## Security

### OIDC Authentication

GitHub Actions authenticate to AWS using OIDC (OpenID Connect) instead of long-lived access keys:

- **Trust Policy**: Scoped to `kmesiab/concept-model-protein-classifier:*`
- **No Secrets**: No AWS credentials stored in GitHub
- **Least Privilege**: Role has only required permissions

### Network Security

- **ALB Security Group**: Allows HTTPS (443) and HTTP (80) from internet
- **ECS Security Group**: Allows port 8000 only from ALB
- **Private Subnets**: ECS tasks run in private subnets with NAT gateway access

### IAM Roles

- **GitHub Actions Role**: ECR push/pull, ECS deploy, CloudWatch logs
- **ECS Task Execution Role**: Pull images, write logs
- **ECS Task Role**: Runtime permissions for the application

## Configuration Variables

Key variables in `variables.tf`:

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | `us-west-2` | AWS region |
| `aws_account_id` | `462498369025` | AWS account ID |
| `environment` | `prod` | Environment name |
| `container_port` | `8000` | Port exposed by container |
| `container_cpu` | `512` | CPU units (0.5 vCPU) |
| `container_memory` | `1024` | Memory in MB |
| `desired_count` | `2` | Number of container instances |

## Scaling

To adjust the number of running containers:

```bash
terraform apply -var="desired_count=4"
```

Or update `variables.tf` and reapply.

## Monitoring

- **CloudWatch Logs**: `/ecs/protein-classifier-api`
- **VPC Flow Logs**: `/aws/vpc/protein-classifier-flow-logs` (7-day retention)
- **ECS Service**: Container Insights enabled
- **Health Checks**: ALB health check on `/health` endpoint

## Cost Optimization

The infrastructure implements several **FinOps best practices** for cost optimization:

### ARM64/Graviton Architecture

ECS tasks run on **AWS Graviton (ARM64)** processors for maximum cost efficiency:

- **CPU Architecture**: ARM64 instead of x86_64
- **Cost Savings**: ~20% reduction on ECS compute costs
- **Performance**: Better price/performance ratio with Graviton processors
- **Sustainability**: ARM-based instances are more energy-efficient
- **Implementation**: Multi-architecture Docker images (linux/amd64, linux/arm64) built automatically

The task definition specifies `runtime_platform.cpu_architecture = ARM64` to leverage Graviton processors.

### S3 Lifecycle Policies

The ALB logs S3 bucket includes three lifecycle policies:

1. **Abort Incomplete Multipart Uploads**: Automatically deletes failed uploads after 7 days
   - **Savings**: 5-10% of S3 costs
2. **Archive Old Versions**: Transitions non-current object versions to Glacier after 30 days, expires after 90 days
   - **Savings**: Up to 97% on archived data
3. **Intelligent-Tiering**: Automatically moves objects between access tiers based on usage patterns
   - **Savings**: 20-40% on infrequently accessed data

### Resource Tagging

All resources include standardized tags for cost allocation:

- `Environment`: "Prod"
- `Service`: "protein-classifier"
- `Project`: "protein-classifier"
- `ManagedBy`: "Terraform"

### VPC Flow Logs

VPC Flow Logs are configured with a 7-day retention period to balance security monitoring with storage costs.

## Troubleshooting

### DynamoDB Table Already Exists Error

If you encounter this error during `terraform apply`:

```text
Error: creating AWS DynamoDB Table (protein-classifier-terraform-locks): 
operation error DynamoDB: CreateTable, https response error StatusCode: 400, 
ResourceInUseException: Table already exists: protein-classifier-terraform-locks
```

This means the DynamoDB table was manually created outside of Terraform management. To fix:

**Option 1: Import the Existing Table (Preferred)**

Use the provided import script:

```bash
cd terraform
./import-dynamodb-table.sh
```

Or manually import:

```bash
cd terraform
terraform import aws_dynamodb_table.terraform_locks protein-classifier-terraform-locks
```

After import, verify with:

```bash
terraform plan  # Should show no changes for DynamoDB table
```

**Option 2: Delete and Recreate (Alternative)**

⚠️ **Warning**: Only use this option if you're sure no other Terraform operations are running.

1. Delete the manually created table in AWS Console
2. Run `terraform apply` to let Terraform create it

### Check ECS Service Status

```bash
aws ecs describe-services \
  --cluster protein-classifier-api-1-0-0-prod-cluster \
  --services protein-classifier-api-service \
  --region us-west-2
```

### View Container Logs

```bash
aws logs tail /ecs/protein-classifier-api \
  --follow \
  --region us-west-2
```

### Check ALB Health

```bash
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names protein-classifier-ecs-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text \
    --region us-west-2) \
  --region us-west-2
```

## Cleanup

To destroy all infrastructure:

```bash
terraform destroy
```

**Warning**: This will delete all resources except the S3 state bucket and Route 53 hosted zone.

## Support

For issues or questions, open an issue in the GitHub repository.
