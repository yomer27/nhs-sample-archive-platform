# ---------------------------
# Package each function's code into a zip Terraform can deploy
# ---------------------------
data "archive_file" "ingest" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/ingest"
  output_path = "${path.module}/../lambda/ingest.zip"
}

data "archive_file" "query" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/query"
  output_path = "${path.module}/../lambda/query.zip"
}

data "archive_file" "retention" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/retention"
  output_path = "${path.module}/../lambda/retention.zip"
}

# ---------------------------
# Ingest Lambda
# ---------------------------
resource "aws_lambda_function" "ingest" {
  function_name    = "ingest-sample-metadata"
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.ingest.arn
  filename         = data.archive_file.ingest.output_path
  source_code_hash = data.archive_file.ingest.output_base64sha256
  timeout          = 10
}

resource "aws_lambda_permission" "allow_s3_invoke_ingest" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data.arn
}

resource "aws_s3_bucket_notification" "data_upload_trigger" {
  bucket = aws_s3_bucket.data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.ingest.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke_ingest]
}

# ---------------------------
# Query Lambda
# ---------------------------
resource "aws_lambda_function" "query" {
  function_name    = "query-sample-by-id"
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.query.arn
  filename         = data.archive_file.query.output_path
  source_code_hash = data.archive_file.query.output_base64sha256
  timeout          = 10
}

# ---------------------------
# Retention Lambda
# ---------------------------
resource "aws_lambda_function" "retention" {
  function_name    = "retention-check"
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.retention.arn
  filename         = data.archive_file.retention.output_path
  source_code_hash = data.archive_file.retention.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      DATA_BUCKET   = aws_s3_bucket.data.bucket
      SNS_TOPIC_ARN = aws_sns_topic.alerts.arn
    }
  }
}
