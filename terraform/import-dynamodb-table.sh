#!/bin/bash

# Script to import the manually created DynamoDB terraform-locks table into Terraform state
# This resolves the error: "Table already exists: protein-classifier-terraform-locks"
#
# Usage:
#   1. Ensure you're in the terraform directory
#   2. Run terraform init first (with dynamodb_table commented out in backend.tf if needed)
#   3. Run this script: ./import-dynamodb-table.sh
#   4. Uncomment dynamodb_table in backend.tf
#   5. Run terraform init --reconfigure

set -e

echo "=========================================="
echo "DynamoDB Terraform Locks Table Import"
echo "=========================================="
echo ""

# Check if we're in the terraform directory
if [ ! -f "dynamodb.tf" ]; then
  echo "❌ Error: This script must be run from the terraform directory"
  echo "   Please run: cd terraform && ./import-dynamodb-table.sh"
  exit 1
fi

# Check if terraform is initialized
if [ ! -d ".terraform" ]; then
  echo "❌ Error: Terraform is not initialized"
  echo "   Please run: terraform init"
  exit 1
fi

echo "🔄 Importing DynamoDB table: protein-classifier-terraform-locks"
echo ""

# Attempt to import the DynamoDB table
# Temporarily disable exit-on-error to capture the exit code
set +e
terraform import aws_dynamodb_table.terraform_locks protein-classifier-terraform-locks
import_exit_code=$?
set -e

if [ $import_exit_code -eq 0 ]; then
  echo ""
  echo "✅ SUCCESS: DynamoDB table imported into Terraform state"
  echo ""
  echo "Next steps:"
  echo "  1. Verify the import: terraform plan"
  echo "     (Should show no changes for the DynamoDB table)"
  echo "  2. If backend.tf has dynamodb_table commented out, uncomment it"
  echo "  3. Reconfigure backend: terraform init --reconfigure"
  echo ""
else
  echo ""
  echo "❌ FAILED: Import failed with exit code $import_exit_code"
  echo ""
  echo "Possible reasons:"
  echo "  • The table is already in Terraform state (check: terraform state list)"
  echo "  • The table doesn't exist in AWS (check AWS console)"
  echo "  • AWS credentials are not configured correctly"
  echo "  • The table name doesn't match: protein-classifier-terraform-locks"
  echo ""
  echo "To check if already imported:"
  echo "  terraform state list | grep terraform_locks"
  echo ""
  exit $import_exit_code
fi
