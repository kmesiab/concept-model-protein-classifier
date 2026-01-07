terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "protein-classifier"
      Application = "protein-classifier-api"
      Environment = var.environment
      Service     = "protein-classifier"
      ManagedBy   = "Terraform"
      Repository  = var.github_repo
      CostCenter  = "protein-classifier"
    }
  }
}
