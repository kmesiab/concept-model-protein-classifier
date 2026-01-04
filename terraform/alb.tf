# Data source for ELB service account (region-specific account for ALB access logs)
data "aws_elb_service_account" "main" {}

# S3 Bucket for ALB Access Logs
resource "aws_s3_bucket" "alb_logs" {
  bucket = "protein-classifier-alb-logs-${var.aws_account_id}"

  tags = {
    Name = "protein-classifier-alb-logs"
  }
}

# S3 Bucket Versioning for ALB Logs
resource "aws_s3_bucket_versioning" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Lifecycle Configuration for Cost Optimization
resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  # Rule 1: Delete incomplete multipart uploads after 7 days
  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Rule 2: Transition non-current versions to Glacier and expire
  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  # Rule 3: Enable Intelligent-Tiering for current objects
  rule {
    id     = "intelligent-tiering"
    status = "Enabled"

    filter {}

    transition {
      days          = 1
      storage_class = "INTELLIGENT_TIERING"
    }
  }
}

# S3 Bucket Public Access Block for ALB logs
resource "aws_s3_bucket_public_access_block" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Logging for ALB logs bucket
resource "aws_s3_bucket_logging" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  target_bucket = aws_s3_bucket.alb_logs.id
  target_prefix = "access-logs/"
}

# Enable server-side encryption for ALB logs bucket with KMS
resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.alb_logs_s3.arn
    }
    bucket_key_enabled = true
  }
}

# Bucket policy to allow ALB to write logs and S3 logging service to write access logs
resource "aws_s3_bucket_policy" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # ALB service can only write to the designated log prefix path
        # Scoped to AWSLogs/<account-id>/* to prevent writes outside the log location
        Sid    = "AWSLogDeliveryWrite"
        Effect = "Allow"
        Principal = {
          Service = "elasticloadbalancing.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/alb-logs/AWSLogs/${var.aws_account_id}/*"
      },
      {
        # ALB requires GetBucketAcl at bucket root to verify permissions
        # This is a required permission per AWS documentation and cannot be further restricted
        Sid    = "AWSLogDeliveryAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "elasticloadbalancing.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.alb_logs.arn
      },
      {
        # Regional ELB service account writes to the same ALB logs prefix
        # Uses parameterized account ID to avoid hardcoding
        Sid    = "ELBAccountWrite"
        Effect = "Allow"
        Principal = {
          AWS = data.aws_elb_service_account.main.arn
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/alb-logs/AWSLogs/${var.aws_account_id}/*"
      },
      {
        # S3 logging service writes to a dedicated access-logs prefix
        # This prevents S3 access logs from mixing with ALB logs
        Sid    = "S3ServerAccessLogsPolicy"
        Effect = "Allow"
        Principal = {
          Service = "logging.s3.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/access-logs/*"
      },
      {
        # S3 logging service requires GetBucketAcl at bucket root
        # Required per AWS documentation for S3 server access logging
        Sid    = "S3ServerAccessLogsAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "logging.s3.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.alb_logs.arn
      }
    ]
  })
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "protein-classifier-alb"
  internal           = false # trivy:ignore:AVD-AWS-0053 - ALB must be public to serve internet traffic
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  enable_deletion_protection = false
  enable_http2               = true
  drop_invalid_header_fields = true

  access_logs {
    # Use .bucket property (bucket name) instead of .id for ALB access logs configuration
    # This ensures ALB can properly reference the bucket for log delivery
    bucket  = aws_s3_bucket.alb_logs.bucket
    prefix  = "alb-logs"
    enabled = true
  }

  tags = {
    Name = "protein-classifier-alb"
  }

  depends_on = [aws_s3_bucket_policy.alb_logs, aws_kms_key_policy.alb_logs_s3]
}

# Target Group for ECS
resource "aws_lb_target_group" "ecs" {
  name        = "protein-classifier-ecs-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 15
    path                = var.health_check_path
    matcher             = "200"
    protocol            = "HTTP"
  }

  deregistration_delay = 30

  tags = {
    Name = "protein-classifier-ecs-tg"
  }
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Ext1-2021-06" # trivy:ignore:AVD-AWS-0047 - Modern policy supporting TLS 1.2 and 1.3
  certificate_arn   = aws_acm_certificate.api.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs.arn
  }

  depends_on = [aws_acm_certificate_validation.api]
}

# HTTP Listener (redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
