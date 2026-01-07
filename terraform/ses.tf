# AWS SES Configuration for Outbound Email
#
# This configuration sets up AWS Simple Email Service (SES) for sending
# outbound email notifications for the Protein Classifier API.
#
# Features:
# - Domain verification for proteinclassifier.com
# - DKIM signing for email authentication
# - Custom MAIL FROM domain for improved deliverability
# - Configuration set for tracking and monitoring

# Note: Route53 zone data source is defined in acm.tf and reused here

# SES Domain Identity
resource "aws_ses_domain_identity" "main" {
  domain = var.domain_name
}

# Route53 record for SES domain verification
resource "aws_route53_record" "ses_verification" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "_amazonses.${var.domain_name}"
  type    = "TXT"
  ttl     = 600
  records = [aws_ses_domain_identity.main.verification_token]
}

# Wait for domain verification
resource "aws_ses_domain_identity_verification" "main" {
  domain = aws_ses_domain_identity.main.id

  depends_on = [aws_route53_record.ses_verification]
}

# Enable DKIM for domain
resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

# Route53 records for DKIM verification (3 records required)
resource "aws_route53_record" "ses_dkim" {
  count   = 3
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "${aws_ses_domain_dkim.main.dkim_tokens[count.index]}._domainkey.${var.domain_name}"
  type    = "CNAME"
  ttl     = 600
  records = ["${aws_ses_domain_dkim.main.dkim_tokens[count.index]}.dkim.amazonses.com"]
}

# Custom MAIL FROM domain for better deliverability
resource "aws_ses_domain_mail_from" "main" {
  domain                 = aws_ses_domain_identity.main.domain
  mail_from_domain       = "mail.${aws_ses_domain_identity.main.domain}"
  behavior_on_mx_failure = "UseDefaultValue"
}

# Route53 MX record for MAIL FROM domain
resource "aws_route53_record" "ses_mail_from_mx" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = aws_ses_domain_mail_from.main.mail_from_domain
  type    = "MX"
  ttl     = 600
  records = ["10 feedback-smtp.${var.aws_region}.amazonses.com"]
}

# Route53 TXT record for SPF (Sender Policy Framework)
resource "aws_route53_record" "ses_mail_from_txt" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = aws_ses_domain_mail_from.main.mail_from_domain
  type    = "TXT"
  ttl     = 600
  records = ["v=spf1 include:amazonses.com ~all"]
}

# SES Configuration Set for email tracking and monitoring
resource "aws_ses_configuration_set" "main" {
  name = "protein-classifier-email"

  delivery_options {
    tls_policy = "Require"
  }

  reputation_metrics_enabled = true
}

# Email identity for noreply address
resource "aws_ses_email_identity" "noreply" {
  email = "noreply@${var.domain_name}"
}

# Outputs for use in application
output "ses_domain_identity_arn" {
  description = "ARN of the SES domain identity"
  value       = aws_ses_domain_identity.main.arn
}

output "ses_configuration_set_name" {
  description = "Name of the SES configuration set"
  value       = aws_ses_configuration_set.main.name
}

output "ses_from_email" {
  description = "From email address for SES"
  value       = "noreply@${var.domain_name}"
}

output "ses_mail_from_domain" {
  description = "MAIL FROM domain for SES"
  value       = aws_ses_domain_mail_from.main.mail_from_domain
}
