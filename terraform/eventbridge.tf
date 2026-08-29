resource "aws_scheduler_schedule" "retention_daily" {
  name                = "retention-check-daily"
  schedule_expression = "rate(1 day)"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.retention.arn
    role_arn = aws_iam_role.scheduler_invoke_retention.arn
  }
}

resource "aws_iam_role" "scheduler_invoke_retention" {
  name = "scheduler-invoke-retention-role-tf"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Action    = "sts:AssumeRole"
        Principal = { Service = "scheduler.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_role_policy" "scheduler_invoke_retention" {
  name = "scheduler-invoke-retention-policy"
  role = aws_iam_role.scheduler_invoke_retention.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.retention.arn
      }
    ]
  })
}
