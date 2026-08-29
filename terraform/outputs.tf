output "api_invoke_url" {
  description = "Base URL for the sample query API"
  value       = aws_apigatewayv2_api.query_api.api_endpoint
}

output "frontend_website_url" {
  description = "URL of the static lookup frontend"
  value       = aws_s3_bucket_website_configuration.site.website_endpoint
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB samples table"
  value       = aws_dynamodb_table.samples.name
}
