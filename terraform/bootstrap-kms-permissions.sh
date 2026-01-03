#!/usr/bin/env bash
#
# Bootstrap KMS Permissions for Terraform State Locking
#
# This script solves the chicken-and-egg problem where:
# 1. Terraform code has KMS permissions defined, but
# 2. Terraform can't run to apply them because it needs those permissions
#    to access the DynamoDB state lock table
#
# This script directly updates the KMS key policy to grant the GitHub Actions
# role the necessary permissions to decrypt the DynamoDB table.
#
# Usage:
#   ./bootstrap-kms-permissions.sh [KMS_KEY_ID] [GITHUB_ACTIONS_ROLE_ARN]
#
# Example:
#   ./bootstrap-kms-permissions.sh \
#     e9b37450-f4df-45d6-a336-aefd3b1d0896 \
#     arn:aws:iam::462498369025:assumed-role/github-actions-terraform/GitHubActions
#
# Or use environment variables:
#   export KMS_KEY_ID=e9b37450-f4df-45d6-a336-aefd3b1d0896
#   export GITHUB_ACTIONS_ROLE_ARN=arn:aws:iam::462498369025:role/github-actions-terraform
#   ./bootstrap-kms-permissions.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values (can be overridden by arguments or environment variables)
KMS_KEY_ID="${1:-${KMS_KEY_ID:-e9b37450-f4df-45d6-a336-aefd3b1d0896}}"
GITHUB_ACTIONS_ROLE_ARN="${2:-${GITHUB_ACTIONS_ROLE_ARN:-arn:aws:iam::462498369025:role/github-actions-terraform}}"
AWS_REGION="${AWS_REGION:-us-west-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-462498369025}"

# Validate required tools
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI is not installed${NC}"
    echo -e "${YELLOW}Install it from: https://aws.amazon.com/cli/${NC}"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ Error: jq is not installed${NC}"
    echo -e "${YELLOW}Install it with: sudo apt-get install jq (Ubuntu) or brew install jq (macOS)${NC}"
    exit 1
fi

# Validate AWS credentials
echo -e "${BLUE}🔍 Validating AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Error: AWS credentials are not configured or invalid${NC}"
    echo -e "${YELLOW}Configure credentials with: aws configure${NC}"
    exit 1
fi

CALLER_IDENTITY=$(aws sts get-caller-identity)
echo -e "${GREEN}✅ AWS credentials validated${NC}"
echo -e "${BLUE}   Identity: $(echo "$CALLER_IDENTITY" | jq -r '.Arn')${NC}"

# Validate KMS key exists
echo -e "${BLUE}🔍 Validating KMS key...${NC}"
if ! aws kms describe-key --key-id "$KMS_KEY_ID" --region "$AWS_REGION" &> /dev/null; then
    echo -e "${RED}❌ Error: KMS key not found: $KMS_KEY_ID${NC}"
    exit 1
fi

KMS_KEY_ARN=$(aws kms describe-key --key-id "$KMS_KEY_ID" --region "$AWS_REGION" --query 'KeyMetadata.Arn' --output text)
echo -e "${GREEN}✅ KMS key validated${NC}"
echo -e "${BLUE}   Key ARN: $KMS_KEY_ARN${NC}"

# Get current KMS key policy
echo -e "${BLUE}🔍 Retrieving current KMS key policy...${NC}"
CURRENT_POLICY=$(aws kms get-key-policy \
    --key-id "$KMS_KEY_ID" \
    --policy-name default \
    --region "$AWS_REGION" \
    --query 'Policy' \
    --output text)

if [ -z "$CURRENT_POLICY" ]; then
    echo -e "${RED}❌ Error: Failed to retrieve current KMS key policy${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Current policy retrieved${NC}"

# Check if GitHub Actions role already has permissions
echo -e "${BLUE}🔍 Checking if GitHub Actions role already has permissions...${NC}"
if echo "$CURRENT_POLICY" | jq -e ".Statement[] | select(.Principal.AWS == \"$GITHUB_ACTIONS_ROLE_ARN\")" &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub Actions role already has a statement in the policy${NC}"
    echo -e "${BLUE}   Checking if permissions are sufficient...${NC}"
    
    EXISTING_ACTIONS=$(echo "$CURRENT_POLICY" | jq -r ".Statement[] | select(.Principal.AWS == \"$GITHUB_ACTIONS_ROLE_ARN\") | .Action | if type == \"array\" then .[] else . end")
    
    if echo "$EXISTING_ACTIONS" | grep -q "kms:Decrypt" && \
       echo "$EXISTING_ACTIONS" | grep -q "kms:DescribeKey" && \
       echo "$EXISTING_ACTIONS" | grep -q "kms:GenerateDataKey"; then
        echo -e "${GREEN}✅ GitHub Actions role already has all required permissions${NC}"
        echo -e "${BLUE}   No action needed. Bootstrap complete!${NC}"
        exit 0
    fi
fi

# Create new policy statement for GitHub Actions
NEW_STATEMENT=$(cat <<EOF
{
  "Sid": "AllowGitHubActionsToUseDynamoDBKey",
  "Effect": "Allow",
  "Principal": {
    "AWS": "$GITHUB_ACTIONS_ROLE_ARN"
  },
  "Action": [
    "kms:Decrypt",
    "kms:DescribeKey",
    "kms:GenerateDataKey",
    "kms:Encrypt"
  ],
  "Resource": "*"
}
EOF
)

# Parse current policy and add new statement
echo -e "${BLUE}🔨 Creating updated policy...${NC}"

# Remove existing statement for GitHub Actions role if it exists (to avoid duplicates)
UPDATED_POLICY=$(echo "$CURRENT_POLICY" | jq --arg arn "$GITHUB_ACTIONS_ROLE_ARN" \
    'del(.Statement[] | select(.Principal.AWS? == $arn))')

# Add new statement
UPDATED_POLICY=$(echo "$UPDATED_POLICY" | jq --argjson stmt "$NEW_STATEMENT" \
    '.Statement += [$stmt]')

# Validate the updated policy is valid JSON
if ! echo "$UPDATED_POLICY" | jq empty 2> /dev/null; then
    echo -e "${RED}❌ Error: Generated policy is not valid JSON${NC}"
    exit 1
fi

# Save the updated policy to a temporary file for review
TEMP_POLICY_FILE=$(mktemp)
echo "$UPDATED_POLICY" > "$TEMP_POLICY_FILE"

echo -e "${GREEN}✅ Updated policy created${NC}"
echo -e "${BLUE}   Policy saved to: $TEMP_POLICY_FILE${NC}"

# Show the diff
echo -e "${BLUE}📋 New statement to be added:${NC}"
echo -e "${YELLOW}$NEW_STATEMENT${NC}"
echo ""

# Prompt for confirmation (unless running in CI)
if [ "${CI:-false}" != "true" ]; then
    echo -e "${YELLOW}⚠️  This will update the KMS key policy${NC}"
    echo -e "${YELLOW}   Press ENTER to continue or Ctrl+C to abort...${NC}"
    read -r
fi

# Apply the updated policy
echo -e "${BLUE}🚀 Applying updated KMS key policy...${NC}"
if aws kms put-key-policy \
    --key-id "$KMS_KEY_ID" \
    --policy-name default \
    --policy "file://$TEMP_POLICY_FILE" \
    --region "$AWS_REGION"; then
    
    echo -e "${GREEN}✅ KMS key policy updated successfully!${NC}"
    echo ""
    echo -e "${GREEN}🎉 Bootstrap complete!${NC}"
    echo -e "${BLUE}   The GitHub Actions role now has permission to:${NC}"
    echo -e "${BLUE}   - kms:Decrypt${NC}"
    echo -e "${BLUE}   - kms:DescribeKey${NC}"
    echo -e "${BLUE}   - kms:GenerateDataKey${NC}"
    echo -e "${BLUE}   - kms:Encrypt${NC}"
    echo ""
    echo -e "${GREEN}✅ Terraform Apply should now work!${NC}"
else
    echo -e "${RED}❌ Error: Failed to update KMS key policy${NC}"
    echo -e "${YELLOW}   Policy file saved at: $TEMP_POLICY_FILE${NC}"
    exit 1
fi

# Clean up
rm -f "$TEMP_POLICY_FILE"
