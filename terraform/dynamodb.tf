# Import existing DynamoDB table into Terraform state
import {
  to = aws_dynamodb_table.terraform_locks
  id = "protein-classifier-terraform-locks"
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "protein-classifier-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "protein-classifier-terraform-locks"
    Description = "DynamoDB table for Terraform state locking"
  }
}
