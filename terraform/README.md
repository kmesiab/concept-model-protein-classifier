# Terraform Infrastructure for Protein Classifier API

This directory contains the Terraform infrastructure code for deploying the Protein Classifier API to AWS ECS Fargate with OIDC authentication.

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
- **ECR Repository**: `protein-classifier-api` for Docker images
- **ECS Cluster**: `protein-classifier-api-1-0-0-prod-cluster`
- **ECS Service**: Fargate service running on port 8000
- **Application Load Balancer**: HTTPS (443) → ECS (8000)
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

### Initial Setup

1. **Initialize Terraform**:

   ```bash
   cd terraform
   terraform init
   ```

2. **Review the plan**:

   ```bash
   terraform plan
   ```

3. **Apply the infrastructure**:

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
- **ECS Service**: Container Insights enabled
- **Health Checks**: ALB health check on `/health` endpoint

## Troubleshooting

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
  --target-group-arn $(terraform output -raw alb_target_group_arn) \
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
