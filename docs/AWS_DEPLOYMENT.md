# AWS ECS Deployment Guide

This guide provides instructions for deploying the Protein Classifier API to AWS ECS Fargate using Terraform and GitHub Actions.

## Prerequisites

### Already Configured

✅ **AWS Account**: `462498369025`  
✅ **Domain**: `proteinclassifier.com` (delegated to Route 53)  
✅ **Route 53 Hosted Zone**: Created with nameservers  
✅ **S3 State Bucket**: `protein-classifier-terraform-state` (us-west-2, versioning enabled, encrypted)  
✅ **GitHub OIDC Provider**: `arn:aws:iam::462498369025:oidc-provider/token.actions.githubusercontent.com`

### Required Tools

- **Terraform** >= 1.0 - [Install Terraform](https://developer.hashicorp.com/terraform/downloads)
- **AWS CLI** - [Install AWS CLI](https://aws.amazon.com/cli/)
- **Git** - For repository management

## Deployment Steps

### 1. Initial Infrastructure Setup

1. **Navigate to the terraform directory**:

   ```bash
   cd terraform
   ```

2. **Initialize Terraform** (downloads providers and configures backend):

   ```bash
   terraform init
   ```

   This will:
   - Download the AWS provider
   - Configure the S3 backend for state storage
   - Set up remote state locking with DynamoDB

3. **Review the planned changes**:

   ```bash
   terraform plan
   ```

   Review the output to ensure all resources will be created as expected.

4. **Apply the infrastructure**:

   ```bash
   terraform apply
   ```

   Type `yes` when prompted to confirm.

   **Expected Creation Time**: ~10-15 minutes (NAT Gateways take the longest)

5. **Save the outputs**:

   ```bash
   terraform output
   ```

   Key outputs:
   - `ecr_repository_url`: ECR repository for Docker images
   - `ecs_cluster_name`: ECS cluster name
   - `ecs_service_name`: ECS service name
   - `api_url`: API endpoint (<https://api.proteinclassifier.com>)
   - `github_actions_role_arn`: IAM role ARN for GitHub Actions

### 2. Verify Infrastructure

1. **Check ECS Cluster**:

   ```bash
   aws ecs describe-clusters \
     --clusters protein-classifier-api-1-0-0-prod-cluster \
     --region us-west-2
   ```

2. **Verify DNS Resolution**:

   ```bash
   nslookup api.proteinclassifier.com
   ```

3. **Check SSL Certificate**:

   ```bash
   aws acm list-certificates --region us-west-2
   ```

### 3. First Deployment via GitHub Actions

The workflows are configured to run automatically, but for the first deployment:

1. **Manually trigger the Docker build**:
   - Go to GitHub repository
   - Navigate to **Actions** → **Build and Push Docker Image**
   - Click **Run workflow** → **Run workflow**

2. **Monitor the build**:
   - Watch the workflow progress
   - Verify the Docker image is pushed to ECR

3. **Automatic ECS deployment**:
   - After successful build, the deploy workflow will automatically trigger
   - It will update the ECS service with the new image

4. **Verify deployment**:

   ```bash
   # Check service status
   aws ecs describe-services \
     --cluster protein-classifier-api-1-0-0-prod-cluster \
     --services protein-classifier-api-service \
     --region us-west-2
   
   # Test the API endpoint
   curl https://api.proteinclassifier.com/health
   ```

### 4. Subsequent Deployments

After the initial setup, deployments are fully automated:

1. **Push changes to main branch**:

   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Automatic workflow execution**:
   - Docker build workflow triggers on push to `main`
   - Docker image is built and pushed to ECR
   - ECS deploy workflow automatically triggers after successful build
   - ECS service is updated with the new image

## GitHub Actions Authentication

The workflows use **OIDC** (OpenID Connect) for AWS authentication:

- ✅ **No AWS credentials** stored in GitHub secrets
- ✅ **Secure**: Short-lived tokens for each workflow run
- ✅ **Least privilege**: Role scoped to specific repository
- ✅ **Automatic**: No manual credential rotation required

### How OIDC Works

1. GitHub Actions requests a token from AWS STS
2. AWS validates the request against the OIDC provider
3. AWS issues temporary credentials
4. Workflow uses credentials to interact with AWS services
5. Credentials expire after workflow completes

## Monitoring and Troubleshooting

### CloudWatch Logs

View container logs:

```bash
aws logs tail /ecs/protein-classifier-api --follow --region us-west-2
```

### ECS Service Events

Check for deployment issues:

```bash
aws ecs describe-services \
  --cluster protein-classifier-api-1-0-0-prod-cluster \
  --services protein-classifier-api-service \
  --region us-west-2 \
  --query 'services[0].events[0:5]'
```

### Target Group Health

Check ALB target health:

```bash
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names protein-classifier-ecs-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text \
    --region us-west-2) \
  --region us-west-2
```

### Common Issues

#### Issue: ECS tasks failing health checks

**Solution**:

- Check CloudWatch logs for errors
- Verify `/health` endpoint is responding on port 8000
- Ensure security groups allow traffic from ALB to ECS tasks

#### Issue: SSL certificate not validating

**Solution**:

- Verify DNS validation records are created in Route 53
- Allow 5-10 minutes for DNS propagation
- Check ACM certificate status in AWS Console

#### Issue: GitHub Actions OIDC authentication fails

**Solution**:

- Verify the IAM role ARN in workflow files
- Check the trust policy on the IAM role
- Ensure the repository name matches the trust policy condition

## Scaling

### Manual Scaling

Update the desired count:

```bash
cd terraform
terraform apply -var="desired_count=4"
```

### Auto Scaling (Future Enhancement)

To enable auto-scaling, add to `ecs.tf`:

```hcl
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu" {
  name               = "cpu-auto-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
```

## Cost Optimization

### Current Configuration Costs (Approximate)

- **ECS Fargate**: ~$30-40/month (2 tasks, 0.5 vCPU, 1GB RAM)
- **Application Load Balancer**: ~$20-25/month
- **NAT Gateways**: ~$65/month base for 2 NAT gateways (HA) **plus** data processing (~$0.045/GB)
  - Base cost: ~$32.40/month per NAT Gateway ($0.045/hour × 720 hours)
  - Data processing costs can significantly increase with higher traffic
- **Data Transfer**: Variable based on usage (includes NAT data processing and egress)
- **Route 53**: ~$0.50/month (hosted zone)
- **Total**: ~$120-140+/month (depending heavily on data transfer volume)

### Cost Reduction Options

1. **Single NAT Gateway** (reduces HA):
   - Remove one NAT gateway
   - Route all private subnets through single NAT
   - Saves ~$35/month

2. **NAT Instances** instead of NAT Gateways:
   - Use t3.nano EC2 instances
   - Saves ~$60/month
   - Requires additional management

3. **Reduce desired count during off-hours**:
   - Use AWS Lambda to scale down at night
   - Can save 30-50% on Fargate costs

## Security Best Practices

### Implemented

✅ ECS tasks run in private subnets  
✅ ALB security group restricts traffic to HTTPS/HTTP  
✅ ECS security group only allows traffic from ALB  
✅ IMDSv2 required for EC2 instances (if applicable)  
✅ Encryption at rest for logs and state  
✅ OIDC authentication for CI/CD  
✅ Least privilege IAM roles

### Recommendations

- Enable AWS GuardDuty for threat detection
- Configure AWS Config for compliance monitoring
- Set up CloudWatch alarms for unusual activity
- Regular security updates to container images
- Implement AWS WAF on the ALB for additional protection

## Disaster Recovery

### Backup Strategy

- **Terraform State**: S3 bucket with versioning enabled
- **Container Images**: ECR with lifecycle policies (keeps last 10 tagged images)
- **Infrastructure as Code**: All infrastructure in version control

### Recovery Procedures

1. **Complete infrastructure loss**:

   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

2. **Service failure**:

   ```bash
   aws ecs update-service \
     --cluster protein-classifier-api-1-0-0-prod-cluster \
     --service protein-classifier-api-service \
     --force-new-deployment \
     --region us-west-2
   ```

## Cleanup

To destroy all infrastructure:

```bash
cd terraform
terraform destroy
```

**Warning**: This will delete:

- ECS cluster and service
- Load balancer and target groups
- VPC and all networking components
- ECR repository (and all images)
- CloudWatch log groups
- IAM roles

**Not deleted**:

- S3 state bucket (manual deletion required)
- Route 53 hosted zone (manual deletion required)
- DynamoDB state lock table (manual deletion required)

## Support

For issues or questions:

- Create an issue in the GitHub repository
- Review CloudWatch logs for error messages
- Check AWS service health dashboard

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [GitHub Actions OIDC with AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
