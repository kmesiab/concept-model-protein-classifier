variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "AWS account ID must be exactly 12 digits."
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "github_repo" {
  description = "GitHub repository in format owner/repo"
  type        = string
  default     = "kmesiab/concept-model-protein-classifier"
}

variable "domain_name" {
  description = "Domain name for the API"
  type        = string
  default     = "proteinclassifier.com"
}

variable "api_subdomain" {
  description = "Subdomain for the API"
  type        = string
  default     = "api"
}

variable "container_port" {
  description = "Port the container exposes"
  type        = number
  default     = 8000
}

variable "container_cpu" {
  description = "CPU units for the container (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "container_memory" {
  description = "Memory for the container in MB"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired number of container instances"
  type        = number
  default     = 2
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health"
}

variable "nat_gateway_count" {
  description = "Number of NAT Gateways to create (1 for cost savings, 2 for high availability)"
  type        = number
  default     = 1

  validation {
    condition     = var.nat_gateway_count == 1 || var.nat_gateway_count == 2
    error_message = "NAT Gateway count must be either 1 (cost savings) or 2 (high availability)."
  }
}
