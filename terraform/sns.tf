resource "aws_sns_topic" "alerts" {
  name = "sample-archive-alerts"
}

variable "alert_email" {
  description = "Email address to subscribe to retention deletion alerts"
  type        = string
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
