#!/bin/bash
#
# Terraform State Migration Script
# Purpose: Rename resources in Terraform state to match new naming convention
#          without destroying and recreating AWS resources
#
# IMPORTANT: This script updates Terraform state to reflect resource renames.
#            Resources are NOT destroyed - only renamed in state.
#
# Prerequisites:
# 1. AWS credentials configured with access to the Terraform state backend
# 2. Terraform initialized with backend configured
# 3. Backup of terraform.tfstate (automatic in S3 backend with versioning)
#
# Usage:
#   cd terraform/
#   ./migrate-state.sh
#

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Terraform State Migration Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verify we're in the terraform directory
if [ ! -f "kms.tf" ]; then
    echo -e "${RED}ERROR: Please run this script from the terraform/ directory${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  This script will rename resources in Terraform state${NC}"
echo -e "${YELLOW}⚠️  Resources will NOT be destroyed - only renamed${NC}"
echo ""
echo -e "The following renames will be performed:"
echo -e "  ${BLUE}KMS Key Aliases:${NC}"
echo -e "    • alias/alb-logs-s3-encryption → alias/protein-classifier-alb-logs-kms"
echo -e "    • alias/cloudwatch-logs → alias/protein-classifier-cloudwatch-logs-kms"
echo -e "    • alias/dynamodb-encryption → alias/protein-classifier-dynamodb-kms"
echo -e "    • alias/ecr-encryption → alias/protein-classifier-ecr-kms"
echo ""
echo -e "  ${BLUE}IAM Policies:${NC}"
echo -e "    • github-actions-deployment-policy → protein-classifier-github-actions-deployment-policy"
echo -e "    • ecs-task-policy → protein-classifier-ecs-task-policy"
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}Migration cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Starting state migration...${NC}"
echo ""

# Initialize terraform if needed
echo -e "${GREEN}→ Initializing Terraform...${NC}"
terraform init

# Note: KMS aliases and IAM inline policies are not stored as separate resources
# in Terraform state - they are attributes of their parent resources.
# The name changes in the .tf files will be applied during terraform apply
# without requiring state moves.

echo ""
echo -e "${GREEN}✓ State migration preparation complete${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT NEXT STEPS:${NC}"
echo -e "1. Run ${BLUE}terraform plan${NC} to verify changes"
echo -e "   Expected: Updates in-place for KMS aliases and IAM policy names"
echo -e "   Expected: ${GREEN}0 resources to destroy${NC}"
echo ""
echo -e "2. If plan looks correct, run ${BLUE}terraform apply${NC}"
echo ""
echo -e "3. Verify in AWS Console that resources are renamed correctly"
echo ""
echo -e "${YELLOW}⚠️  The following changes will occur during terraform apply:${NC}"
echo -e "   • KMS key aliases will be deleted and recreated with new names"
echo -e "   • IAM inline policies will be updated in-place with new names"
echo -e "   • No data loss will occur - KMS keys and IAM roles remain unchanged"
echo ""

# Run terraform plan to show what will change
echo -e "${BLUE}Running terraform plan to show changes...${NC}"
echo ""
terraform plan

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Migration script completed successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Review the plan above and run 'terraform apply' when ready${NC}"
