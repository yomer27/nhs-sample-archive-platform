#!/bin/bash
#
# run.sh - wrapper for running the retention-checker container from cron.
#
# Expects AWS credentials to already be available on the host, either via
# `aws configure` (mounted below) or an instance IAM role.
#
# Example crontab entry (run daily at 02:00):
#   0 2 * * * /home/ubuntu/retention-checker/run.sh >> /home/ubuntu/retention-checker/logs/run.log 2>&1

set -euo pipefail

IMAGE_NAME="retention-checker:latest"
LOG_DIR="$(dirname "$0")/logs"
mkdir -p "$LOG_DIR"

echo "=== Run started: $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="

docker run --rm \
  -e BUCKET_NAME="your-bucket-name-here" \
  -e RETENTION_DAYS="30" \
  -e AWS_REGION="eu-west-2" \
  -e DRY_RUN="true" \
  -v "$HOME/.aws:/root/.aws:ro" \
  "$IMAGE_NAME"

echo "=== Run finished: $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="
