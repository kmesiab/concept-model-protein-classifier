# IMPORTANT: Bootstrap Process for First-Time Setup
#
# On first run, terraform init will fail because the DynamoDB table
# referenced below does not exist yet. Follow this process:
#
# 1. Comment out the 'dynamodb_table' line below
# 2. Run: terraform init
# 3. Run: terraform apply --target=aws_dynamodb_table.terraform_locks
# 4. Uncomment the 'dynamodb_table' line
# 5. Run: terraform init --reconfigure
#
# See terraform/README.md for detailed bootstrap instructions.

terraform {
  backend "s3" {
    bucket = "protein-classifier-terraform-state"
    key    = "protein-classifier/terraform.tfstate"
    region = "us-west-2"
    dynamodb_table = "protein-classifier-terraform-locks"
    encrypt = true
  }
}
