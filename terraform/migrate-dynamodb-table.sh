#!/bin/bash

# Migration script for DynamoDB Terraform state lock table
# Handles transition from old table name (prop-insights-terraform-lock) 
# to new standardized name (protein-classifier-terraform-locks)
#
# Usage:
#   cd terraform
#   ./migrate-dynamodb-table.sh
#
# This script will:
# 1. Check if old table exists
# 2. Check if new table exists
# 3. Create new table using Terraform if needed
# 4. Import new table into Terraform state
# 5. Optionally delete old table after confirmation

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Table names
OLD_TABLE="prop-insights-terraform-lock"
NEW_TABLE="protein-classifier-terraform-locks"
AWS_REGION="us-west-2"

echo "=========================================="
echo "DynamoDB State Lock Table Migration"
echo "=========================================="
echo ""
echo "Old table: ${OLD_TABLE}"
echo "New table: ${NEW_TABLE}"
echo "Region: ${AWS_REGION}"
echo ""

# Check if we're in the terraform directory
if [ ! -f "dynamodb.tf" ]; then
  echo -e "${RED}❌ Error: This script must be run from the terraform directory${NC}"
  echo "   Please run: cd terraform && ./migrate-dynamodb-table.sh"
  exit 1
fi

# Function to check if a DynamoDB table exists
check_table_exists() {
  local table_name=$1
  aws dynamodb describe-table --table-name "$table_name" --region "$AWS_REGION" &>/dev/null
  return $?
}

# Function to get table status
get_table_status() {
  local table_name=$1
  aws dynamodb describe-table --table-name "$table_name" --region "$AWS_REGION" \
    --query 'Table.TableStatus' --output text 2>/dev/null || echo "NOT_FOUND"
}

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
if ! aws sts get-caller-identity --region "$AWS_REGION" &>/dev/null; then
  echo -e "${RED}❌ Error: AWS credentials not configured or invalid${NC}"
  echo "   Please configure AWS credentials before running this script"
  exit 1
fi

CALLER_IDENTITY=$(aws sts get-caller-identity --region "$AWS_REGION" --output text)
echo -e "${GREEN}✅ AWS credentials valid${NC}"
echo "   Identity: $CALLER_IDENTITY"
echo ""

# Check status of both tables
echo "🔍 Checking current table status..."
OLD_TABLE_STATUS=$(get_table_status "$OLD_TABLE")
NEW_TABLE_STATUS=$(get_table_status "$NEW_TABLE")

echo "   Old table ($OLD_TABLE): $OLD_TABLE_STATUS"
echo "   New table ($NEW_TABLE): $NEW_TABLE_STATUS"
echo ""

# Determine migration path based on table status
if [ "$OLD_TABLE_STATUS" = "NOT_FOUND" ] && [ "$NEW_TABLE_STATUS" = "NOT_FOUND" ]; then
  echo -e "${YELLOW}⚠️  Neither table exists - this is a fresh setup${NC}"
  echo ""
  echo "Follow the bootstrap process:"
  echo "1. Comment out 'dynamodb_table' line in backend.tf"
  echo "2. Run: terraform init"
  echo "3. Run: terraform apply -target=aws_dynamodb_table.terraform_locks"
  echo "4. Uncomment 'dynamodb_table' line in backend.tf"
  echo "5. Run: terraform init -reconfigure"
  exit 0
  
elif [ "$OLD_TABLE_STATUS" = "NOT_FOUND" ] && [ "$NEW_TABLE_STATUS" != "NOT_FOUND" ]; then
  echo -e "${GREEN}✅ Migration already complete!${NC}"
  echo "   The new table ($NEW_TABLE) exists and is in $NEW_TABLE_STATUS status"
  echo "   The old table ($OLD_TABLE) does not exist"
  echo ""
  echo "Next steps:"
  echo "1. Ensure 'dynamodb_table' line is uncommented in backend.tf"
  echo "2. Run: terraform init -reconfigure"
  echo "3. Run: terraform plan (should show no changes for DynamoDB table)"
  exit 0
  
elif [ "$OLD_TABLE_STATUS" != "NOT_FOUND" ] && [ "$NEW_TABLE_STATUS" != "NOT_FOUND" ]; then
  echo -e "${YELLOW}⚠️  Both tables exist - cleanup required${NC}"
  echo ""
  echo "This situation requires manual intervention:"
  echo "1. Verify the new table ($NEW_TABLE) is working with Terraform"
  echo "2. Check if any other systems are using the old table ($OLD_TABLE)"
  echo "3. If safe, delete the old table manually:"
  echo "   aws dynamodb delete-table --table-name $OLD_TABLE --region $AWS_REGION"
  exit 0
  
elif [ "$OLD_TABLE_STATUS" != "NOT_FOUND" ] && [ "$NEW_TABLE_STATUS" = "NOT_FOUND" ]; then
  echo -e "${BLUE}🔄 Migration required: Old table exists, new table does not${NC}"
  echo ""
  
  # This is the main migration scenario
  echo "Starting migration process..."
  echo ""
  
  # Step 1: Verify Terraform is NOT initialized with state locking
  echo "Step 1: Checking Terraform initialization..."
  if [ -d ".terraform" ]; then
    # Check backend configuration by looking at backend.tf directly
    if grep -q "^[[:space:]]*dynamodb_table[[:space:]]*=" backend.tf; then
      echo -e "${YELLOW}⚠️  Warning: backend.tf has dynamodb_table enabled${NC}"
      echo "   This will likely fail during init. We'll reconfigure the backend."
      echo ""
    fi
  fi
  
  # Step 2: Temporarily disable state locking in backend.tf
  echo "Step 2: Temporarily disabling state locking..."
  if grep -q "^[[:space:]]*dynamodb_table[[:space:]]*=" backend.tf; then
    echo "   Creating backup of backend.tf..."
    cp backend.tf backend.tf.backup
    echo "   Commenting out dynamodb_table line..."
    # Pattern: Adds "# " before dynamodb_table and appends comment marker
    # Example: "    dynamodb_table = ..." becomes "    # dynamodb_table = ...  # TEMP: Disabled for migration"
    sed -i.tmp 's/^\([[:space:]]*\)dynamodb_table\([[:space:]]*=.*\)/\1# dynamodb_table\2  # TEMP: Disabled for migration/' backend.tf
    rm -f backend.tf.tmp
    echo -e "${GREEN}✅ State locking temporarily disabled${NC}"
  else
    echo "   dynamodb_table line already commented out or not found"
  fi
  echo ""
  
  # Step 3: Initialize Terraform without state locking
  echo "Step 3: Initializing Terraform without state locking..."
  if terraform init -reconfigure; then
    echo -e "${GREEN}✅ Terraform initialized successfully${NC}"
  else
    echo -e "${RED}❌ Terraform init failed${NC}"
    echo "   Restoring backend.tf from backup..."
    [ -f backend.tf.backup ] && mv backend.tf.backup backend.tf
    exit 1
  fi
  echo ""
  
  # Step 4: Create new DynamoDB table using Terraform
  echo "Step 4: Creating new DynamoDB table using Terraform..."
  echo "   Running: terraform apply -target=aws_dynamodb_table.terraform_locks"
  echo ""
  
  if terraform apply -target=aws_dynamodb_table.terraform_locks -auto-approve; then
    echo ""
    echo -e "${GREEN}✅ New DynamoDB table created successfully${NC}"
  else
    echo ""
    echo -e "${RED}❌ Failed to create new DynamoDB table${NC}"
    echo "   Restoring backend.tf from backup..."
    [ -f backend.tf.backup ] && mv backend.tf.backup backend.tf
    exit 1
  fi
  echo ""
  
  # Step 5: Re-enable state locking in backend.tf
  echo "Step 5: Re-enabling state locking..."
  if [ -f backend.tf.backup ]; then
    echo "   Restoring original backend.tf..."
    mv backend.tf.backup backend.tf
    echo -e "${GREEN}✅ State locking re-enabled${NC}"
  else
    echo "   Uncommenting dynamodb_table line..."
    # Pattern: Removes "# " prefix and the temporary comment marker
    # Preserves original indentation captured in group \1
    # Example: "    # dynamodb_table = ...  # TEMP: Disabled for migration" becomes "    dynamodb_table = ..."
    sed -i.tmp 's/^\([[:space:]]*\)# \(dynamodb_table[[:space:]]*=.*\)[[:space:]]*#.*TEMP:.*migration/\1\2/' backend.tf
    rm -f backend.tf.tmp
    echo -e "${GREEN}✅ State locking re-enabled${NC}"
  fi
  echo ""
  
  # Step 6: Reconfigure backend with state locking
  echo "Step 6: Reconfiguring Terraform backend with state locking..."
  if terraform init -reconfigure; then
    echo -e "${GREEN}✅ Terraform backend reconfigured successfully${NC}"
  else
    echo -e "${RED}❌ Terraform init -reconfigure failed${NC}"
    exit 1
  fi
  echo ""
  
  # Step 7: Verify new table is working
  echo "Step 7: Verifying new table is working..."
  if check_table_exists "$NEW_TABLE"; then
    NEW_TABLE_FINAL_STATUS=$(get_table_status "$NEW_TABLE")
    echo -e "${GREEN}✅ New table exists and is $NEW_TABLE_FINAL_STATUS${NC}"
  else
    echo -e "${RED}❌ New table not found${NC}"
    exit 1
  fi
  echo ""
  
  # Step 8: Ask about old table cleanup
  echo "Step 8: Old table cleanup..."
  echo ""
  echo -e "${YELLOW}The old table ($OLD_TABLE) still exists in AWS.${NC}"
  echo "Do you want to delete it? (yes/no)"
  read -r CONFIRM_DELETE
  
  if [ "$CONFIRM_DELETE" = "yes" ]; then
    echo ""
    echo "Deleting old table..."
    if aws dynamodb delete-table --table-name "$OLD_TABLE" --region "$AWS_REGION"; then
      echo -e "${GREEN}✅ Old table deleted successfully${NC}"
    else
      echo -e "${YELLOW}⚠️  Failed to delete old table${NC}"
      echo "   You may need to delete it manually:"
      echo "   aws dynamodb delete-table --table-name $OLD_TABLE --region $AWS_REGION"
    fi
  else
    echo ""
    echo -e "${YELLOW}Old table not deleted. To delete it later, run:${NC}"
    echo "   aws dynamodb delete-table --table-name $OLD_TABLE --region $AWS_REGION"
  fi
  echo ""
  
  # Success message
  echo "=========================================="
  echo -e "${GREEN}✅ Migration completed successfully!${NC}"
  echo "=========================================="
  echo ""
  echo "Summary:"
  echo "  ✅ New table created: $NEW_TABLE"
  echo "  ✅ Terraform backend reconfigured"
  echo "  ✅ State locking enabled"
  echo ""
  echo "Next steps:"
  echo "  1. Run: terraform plan"
  echo "     (Should show no changes for DynamoDB table)"
  echo "  2. Your Terraform workflows should now work correctly"
  echo ""
  
fi
