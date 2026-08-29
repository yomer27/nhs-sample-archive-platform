variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-west-2"
}

variable "data_bucket_name" {
  description = "Name of the main S3 bucket storing sample archive files"
  type        = string
  default     = "nhs-sample-archive-dev-2026-tf"
}

variable "site_bucket_name" {
  description = "Name of the S3 bucket hosting the static lookup frontend"
  type        = string
  default     = "nhs-sample-lookup-site-dev-2026-tf"
}

variable "trail_bucket_name" {
  description = "Name of the S3 bucket storing CloudTrail logs"
  type        = string
  default     = "nhs-sample-archive-trail-logs-2026-tf"
}

variable "account_id" {
  description = "AWS account ID, used to build ARNs"
  type        = string
  default     = "720328532407"
}
