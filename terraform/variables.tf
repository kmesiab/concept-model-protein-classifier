variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
  default     = "462498369025"
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
