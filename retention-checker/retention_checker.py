"""
Retention Checker

Self-hosted companion to the project's serverless Lambda retention automation.
Scans an S3 bucket for objects older than a retention threshold and logs
what it finds. Designed to run inside a Docker container on a schedule
(via cron) on a Linux host, as a self-managed counterpart to the
serverless (Lambda) retention flow already in this repo.

Environment variables:
    BUCKET_NAME        - S3 bucket to scan (required)
    RETENTION_DAYS      - age threshold in days (default: 30)
    AWS_REGION          - AWS region (default: eu-west-2)
    DRY_RUN             - "true" (default) logs only; "false" would allow
                          real deletion logic to be added later
"""

import os
import sys
import logging
from datetime import datetime, timezone

import boto3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("retention_checker")


def get_config():
    bucket = os.environ.get("BUCKET_NAME")
    if not bucket:
        log.error("BUCKET_NAME environment variable is required.")
        sys.exit(1)

    retention_days = int(os.environ.get("RETENTION_DAYS", "30"))
    region = os.environ.get("AWS_REGION", "eu-west-2")
    dry_run = os.environ.get("DRY_RUN", "true").lower() != "false"

    return bucket, retention_days, region, dry_run


def find_expired_objects(s3_client, bucket, retention_days):
    now = datetime.now(timezone.utc)
    expired = []

    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            age_days = (now - obj["LastModified"]).days
            if age_days >= retention_days:
                expired.append(
                    {
                        "Key": obj["Key"],
                        "AgeDays": age_days,
                        "SizeBytes": obj["Size"],
                    }
                )
    return expired


def main():
    bucket, retention_days, region, dry_run = get_config()

    log.info(
        "Starting retention check | bucket=%s | retention_days=%s | region=%s | dry_run=%s",
        bucket, retention_days, region, dry_run,
    )

    s3 = boto3.client("s3", region_name=region)

    try:
        expired = find_expired_objects(s3, bucket, retention_days)
    except Exception as exc:
        log.exception("Failed to scan bucket '%s': %s", bucket, exc)
        sys.exit(1)

    if not expired:
        log.info("No objects older than %s days found. Nothing to flag.", retention_days)
        return

    log.info("Found %d object(s) past the %d-day retention threshold:", len(expired), retention_days)
    for item in expired:
        log.info(
            "  - %s (age: %d days, size: %d bytes)",
            item["Key"], item["AgeDays"], item["SizeBytes"],
        )

    if dry_run:
        log.info("DRY_RUN is enabled - no objects were modified or deleted.")
    else:
        # Deliberately left as a manual extension point rather than wired up
        # by default: any real deletion path should soft-delete (e.g. move
        # to a "expired/" prefix or tag the object) and log an audit trail,
        # mirroring the approach used in the Lambda retention function.
        log.warning(
            "DRY_RUN is disabled but no deletion logic is implemented yet. "
            "No action was taken."
        )


if __name__ == "__main__":
    main()
