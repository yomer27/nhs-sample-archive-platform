# Small, fast-building base image
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY retention_checker.py .

# Runtime config is supplied via environment variables at `docker run` time
# (BUCKET_NAME, RETENTION_DAYS, AWS_REGION, DRY_RUN) - see run.sh
ENTRYPOINT ["python", "retention_checker.py"]
