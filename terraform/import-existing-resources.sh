#!/bin/bash

# Script to import existing AWS resources into Terraform state
# Run this from the terraform directory after terraform init

set -e

echo "Starting import of existing AWS resources..."

# Import IAM Roles
echo "Importing IAM roles..."
terraform import aws_iam_role.github_actions protein-classifier-github-actions-role || true
terraform import aws_iam_role.ecs_task_execution_role protein-classifier-ecs-task-execution-role || true
terraform import aws_iam_role.ecs_task_role protein-classifier-ecs-task-role || true
terraform import aws_iam_role.vpc_flow_logs protein-classifier-vpc-flow-logs-role || true

# Import S3 Buckets
echo "Importing S3 buckets..."
terraform import aws_s3_bucket.alb_logs protein-classifier-alb-logs-462498369025 || true

# Import Load Balancer Target Groups
echo "Importing ALB target groups..."
# Need to get the ARN for the target group - will need to query AWS
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --names protein-classifier-ecs-tg --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || echo "")
if [ -n "$TARGET_GROUP_ARN" ]; then
  terraform import aws_lb_target_group.ecs "$TARGET_GROUP_ARN" || true
else
  echo "Target group not found or AWS CLI not configured"
fi

# Import KMS Keys - these require the key ID
echo "Importing KMS keys..."
echo "Note: KMS keys need to be imported with their key ID. You'll need to find these manually:"
echo "aws kms list-aliases --query 'Aliases[?AliasName==\`alias/protein-classifier-alb-logs\`].TargetKeyId' --output text"
echo "aws kms list-aliases --query 'Aliases[?AliasName==\`alias/protein-classifier-cloudwatch\`].TargetKeyId' --output text"
echo "aws kms list-aliases --query 'Aliases[?AliasName==\`alias/protein-classifier-dynamodb\`].TargetKeyId' --output text"
echo "aws kms list-aliases --query 'Aliases[?AliasName==\`alias/protein-classifier-ecr\`].TargetKeyId' --output text"
echo ""
echo "Then run:"
echo "terraform import aws_kms_key.alb_logs_s3 <key-id>"
echo "terraform import aws_kms_key.cloudwatch_logs <key-id>"
echo "terraform import aws_kms_key.dynamodb <key-id>"
echo "terraform import aws_kms_key.ecr <key-id>"

echo ""
echo "Import process completed. Check for any errors above."
echo "Run 'terraform plan' to see if there are any remaining resources to import."
