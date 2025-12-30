terraform {
  backend "s3" {
    bucket         = "protein-classifier-terraform-state"
    key            = "protein-classifier/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "protein-classifier-terraform-locks"
    encrypt        = true
  }
}
