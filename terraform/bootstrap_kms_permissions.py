#!/usr/bin/env python3
"""
Bootstrap KMS Permissions for Terraform State Locking

This script solves the chicken-and-egg problem where:
1. Terraform code has KMS permissions defined, but
2. Terraform can't run to apply them because it needs those permissions
   to access the DynamoDB state lock table

This script directly updates the KMS key policy to grant the GitHub Actions
role the necessary permissions to decrypt the DynamoDB table.

Usage:
    python3 bootstrap_kms_permissions.py [--key-id KMS_KEY_ID] [--role-arn ROLE_ARN]

Example:
    python3 bootstrap_kms_permissions.py \
        --key-id e9b37450-f4df-45d6-a336-aefd3b1d0896 \
        --role-arn arn:aws:iam::462498369025:role/github-actions-terraform

Or use environment variables:
    export KMS_KEY_ID=e9b37450-f4df-45d6-a336-aefd3b1d0896
    export GITHUB_ACTIONS_ROLE_ARN=arn:aws:iam::462498369025:role/github-actions-terraform
    python3 bootstrap_kms_permissions.py
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("❌ Error: boto3 is not installed")
    print("Install it with: pip install boto3")
    sys.exit(1)


# ANSI color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def print_color(message: str, color: str = NC) -> None:
    """Print a message with color."""
    print(f"{color}{message}{NC}")


def validate_aws_credentials() -> Dict[str, Any]:
    """Validate AWS credentials are configured."""
    print_color("🔍 Validating AWS credentials...", BLUE)

    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print_color("✅ AWS credentials validated", GREEN)
        print_color(f"   Identity: {identity['Arn']}", BLUE)
        return identity
    except NoCredentialsError:
        print_color("❌ Error: AWS credentials are not configured", RED)
        print_color("Configure credentials with: aws configure", YELLOW)
        sys.exit(1)
    except ClientError as e:
        print_color(f"❌ Error validating credentials: {e}", RED)
        sys.exit(1)


def validate_kms_key(key_id: str, region: str) -> str:
    """Validate KMS key exists and return its ARN."""
    print_color("🔍 Validating KMS key...", BLUE)

    try:
        kms = boto3.client("kms", region_name=region)
        response = kms.describe_key(KeyId=key_id)
        key_arn = response["KeyMetadata"]["Arn"]
        print_color("✅ KMS key validated", GREEN)
        print_color(f"   Key ARN: {key_arn}", BLUE)
        return key_arn
    except ClientError as e:
        print_color(f"❌ Error: KMS key not found: {key_id}", RED)
        print_color(f"   {e}", RED)
        sys.exit(1)


def get_current_policy(key_id: str, region: str) -> Dict[str, Any]:
    """Retrieve the current KMS key policy."""
    print_color("🔍 Retrieving current KMS key policy...", BLUE)

    try:
        kms = boto3.client("kms", region_name=region)
        response = kms.get_key_policy(KeyId=key_id, PolicyName="default")
        policy = json.loads(response["Policy"])
        print_color("✅ Current policy retrieved", GREEN)
        return policy
    except ClientError as e:
        print_color(f"❌ Error retrieving policy: {e}", RED)
        sys.exit(1)


def check_existing_permissions(policy: Dict[str, Any], role_arn: str) -> bool:
    """Check if the GitHub Actions role already has sufficient permissions."""
    print_color("🔍 Checking if GitHub Actions role already has permissions...", BLUE)

    required_actions = {
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey",
    }

    for statement in policy.get("Statement", []):
        principal = statement.get("Principal", {})
        if isinstance(principal, dict):
            aws_principal = principal.get("AWS", "")
            if aws_principal == role_arn:
                print_color(
                    "⚠️  GitHub Actions role already has a statement in the policy",
                    YELLOW,
                )

                actions = statement.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]

                existing_actions = set(actions)
                if required_actions.issubset(existing_actions):
                    print_color(
                        "✅ GitHub Actions role already has all required permissions",
                        GREEN,
                    )
                    print_color("   No action needed. Bootstrap complete!", BLUE)
                    return True

    return False


def create_updated_policy(policy: Dict[str, Any], role_arn: str) -> Dict[str, Any]:
    """Create an updated policy with GitHub Actions permissions."""
    print_color("🔨 Creating updated policy...", BLUE)

    # Remove existing statement for GitHub Actions role if it exists
    new_statements: List[Dict[str, Any]] = []
    for statement in policy.get("Statement", []):
        principal = statement.get("Principal", {})
        if isinstance(principal, dict):
            aws_principal = principal.get("AWS", "")
            if aws_principal != role_arn:
                new_statements.append(statement)
        else:
            new_statements.append(statement)

    # Add new statement
    new_statement = {
        "Sid": "AllowGitHubActionsToUseDynamoDBKey",
        "Effect": "Allow",
        "Principal": {"AWS": role_arn},
        "Action": [
            "kms:Decrypt",
            "kms:DescribeKey",
            "kms:GenerateDataKey",
            "kms:Encrypt",
        ],
        "Resource": "*",
    }

    new_statements.append(new_statement)

    updated_policy = {"Version": "2012-10-17", "Statement": new_statements}

    print_color("✅ Updated policy created", GREEN)
    return updated_policy


def apply_policy(key_id: str, policy: Dict[str, Any], region: str) -> None:
    """Apply the updated policy to the KMS key."""
    print_color("🚀 Applying updated KMS key policy...", BLUE)

    try:
        kms = boto3.client("kms", region_name=region)
        kms.put_key_policy(KeyId=key_id, PolicyName="default", Policy=json.dumps(policy))

        print_color("✅ KMS key policy updated successfully!", GREEN)
        print()
        print_color("🎉 Bootstrap complete!", GREEN)
        print_color("   The GitHub Actions role now has permission to:", BLUE)
        print_color("   - kms:Decrypt", BLUE)
        print_color("   - kms:DescribeKey", BLUE)
        print_color("   - kms:GenerateDataKey", BLUE)
        print_color("   - kms:Encrypt", BLUE)
        print()
        print_color("✅ Terraform Apply should now work!", GREEN)
    except ClientError as e:
        print_color(f"❌ Error updating policy: {e}", RED)
        sys.exit(1)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Bootstrap KMS permissions for Terraform state locking"
    )
    parser.add_argument(
        "--key-id",
        default=os.environ.get("KMS_KEY_ID", "e9b37450-f4df-45d6-a336-aefd3b1d0896"),
        help="KMS key ID (default: from KMS_KEY_ID env var or hardcoded default)",
    )
    parser.add_argument(
        "--role-arn",
        default=os.environ.get(
            "GITHUB_ACTIONS_ROLE_ARN",
            "arn:aws:iam::462498369025:role/github-actions-terraform",
        ),
        help="GitHub Actions role ARN (default: from GITHUB_ACTIONS_ROLE_ARN env var)",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_REGION", "us-west-2"),
        help="AWS region (default: from AWS_REGION env var or us-west-2)",
    )

    args = parser.parse_args()

    # Validate credentials
    validate_aws_credentials()

    # Validate KMS key
    validate_kms_key(args.key_id, args.region)

    # Get current policy
    current_policy = get_current_policy(args.key_id, args.region)

    # Check if permissions already exist
    if check_existing_permissions(current_policy, args.role_arn):
        return

    # Create updated policy
    updated_policy = create_updated_policy(current_policy, args.role_arn)

    # Show the new statement
    print_color("📋 New statement to be added:", BLUE)
    for statement in updated_policy["Statement"]:
        if statement.get("Sid") == "AllowGitHubActionsToUseDynamoDBKey":
            print_color(json.dumps(statement, indent=2), YELLOW)
    print()

    # Prompt for confirmation (unless running in CI)
    if os.environ.get("CI", "false") != "true":
        print_color("⚠️  This will update the KMS key policy", YELLOW)
        print_color("   Press ENTER to continue or Ctrl+C to abort...", YELLOW)
        input()

    # Apply the policy
    apply_policy(args.key_id, updated_policy, args.region)


if __name__ == "__main__":
    main()
