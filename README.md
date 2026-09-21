# NHS Sample Archive Platform

A serverless AWS system for tracking archived laboratory samples (blocks and slides) across two fictional hospital sites, built as a cloud engineering portfolio project following AWS Solutions Architect Associate certification.

**All data in this project is synthetic.** No real patient, specimen, or NHS operational data is used anywhere. The two sending hospital names (QEH, Heartlands) are real Birmingham hospitals, used only as plausible origin labels; the archive sites (Highgate, Kingswood) and every sample record are entirely fictional.

---

## Why I built this

I've spent several years working in NHS laboratories, including time on sample archiving, and I saw firsthand how quickly physical storage fills up. Blocks and slides accumulate fast, and every year or so space pressures meant things had to be reorganised or moved, all tracked manually. That experience is what shaped this project: a fictional, cloud-based version of the same problem, where storage tiering, retention, and lookup are automated rather than manual, and nothing physically needs to be relocated as it ages.

## The idea

Modelled loosely on real histopathology archive workflows (blocks and slides sent from hospitals to a long-term archive, tracked by ID, retained for a fixed period, and eventually retired), this project demonstrates:

- Event-driven serverless architecture (S3 → Lambda → DynamoDB)
- A public lookup API and frontend (API Gateway → Lambda → DynamoDB)
- Automated, policy-driven data lifecycle management (S3 lifecycle rules + a scheduled retention/soft-delete Lambda)
- Least-privilege IAM, scoped per function
- Full observability (CloudTrail, SNS alerting)
- Infrastructure as Code (the entire stack rebuilt in Terraform after the manual build)

## Architecture

*(Diagram: `docs/architecture-diagram.png`, built in diagrams.net using official AWS icons)*

| Component | Purpose |
|---|---|
| **S3** | Stores sample files under `{archiveSite}/{blocks\|slides}/`, versioned, prefix-scoped lifecycle rules transition objects Standard → Standard-IA (30d) → Glacier (90d) |
| **DynamoDB** (`Samples` table) | Metadata index: sample ID (partition key), type, hospital, archive site, upload date, S3 location, storage class, status. GSI on `sendingHospital` for hospital-level queries |
| **Ingest Lambda** | Triggered on S3 upload, parses the object key, writes the metadata record |
| **Query Lambda + API Gateway** | Public `GET /samples/{sampleId}` endpoint, returns the record or a clean 404 |
| **Retention Lambda + EventBridge Scheduler** | Runs daily, retires samples past their retention limit: deletes the S3 object, marks the DynamoDB record `Deleted` with a reason and date (soft delete / tombstone, not a hard delete) |
| **Static frontend** | Single-page lookup tool (S3 static website hosting), calls the API directly |
| **CloudTrail** | Account-wide audit trail of management events |
| **SNS** | Email alert whenever the retention Lambda retires a sample |
| **IAM** | One execution role per Lambda, each scoped to only the actions it needs |

## Data model

Two real Birmingham hospitals (used here only as origin labels for the synthetic samples), each mapped to a fictional archive site:

| Hospital | Archive site | S3 prefix |
|---|---|---|
| Queen Elizabeth Hospital (QEH) | Highgate Archive | `highgate/` |
| Heartlands Hospital (HGH) | Kingswood Archive | `kingswood/` |

Sample IDs follow `{TYPE}-{HOSPITAL}-{YEAR}-{SEQ}`, e.g. `BLK-QEH-2026-0001`, `SLD-HGH-2025-0014`. Each hospital keeps its own independent sequence per sample type per year, matching how real lab accession numbering works (one shared numbering scheme across sites would be unrealistic).

**Retention periods** (illustrative, loosely modelled on general histopathology retention guidance, not a compliance implementation):
- Slides: 10 years
- Blocks: 15 years

When a sample's retention period expires, the retention Lambda deletes the underlying S3 object but keeps the DynamoDB record, updating its status to `Deleted` with a `deletionReason` and `deletedDate`. A lookup on an expired sample doesn't return a bare 404, it confirms the sample existed, was archived correctly, and was destroyed on schedule under a defined policy. This was a deliberate design choice over hard deletion, for audit and governance reasons.

## Build process

This project was built in two phases:

1. **Manual build** (AWS Console): every service configured and verified by hand, to understand and be able to speak to each setting. Screenshots in `docs/images/manual-build/`.
2. **Terraform rebuild**: the identical architecture rebuilt entirely as code, applied, tested, and destroyed. Screenshots in `docs/images/terraform-build/`.

Both phases were fully torn down after verification; nothing in this repo is currently deployed.

## Extension: self-hosted retention checker

Alongside the serverless retention Lambda, this project includes a self-hosted equivalent, built to gain hands-on experience with traditional server-based deployment rather than relying solely on serverless.

A Python script (`retention-checker/retention_checker.py`) scans the S3 bucket for objects past a configurable retention threshold and logs its findings (dry-run by default, no deletion logic wired up). It runs the same way a real operations team might run a scheduled housekeeping job:

- **Linux (Ubuntu on EC2)**: provisioned and administered via SSH
- **Docker**: the script is containerised for portable, repeatable execution
- **Bash + cron**: a wrapper script (`run.sh`) runs the container daily
- **GitHub Actions**: a CI/CD pipeline (`.github/workflows/docker-build.yml`) builds and pushes the image to Docker Hub automatically on every commit touching `retention-checker/`

This isn't meant to replace the serverless Lambda flow, it's a deliberate side-by-side comparison: the Lambda approach needs no infrastructure management but is bound to AWS's event/scheduling model, while this approach is more portable and gives full control over the runtime, at the cost of having to manage the server yourself.

Like the rest of the project, all infrastructure (EC2 instance, S3 bucket) was torn down after verification.

## Design decisions worth noting

- **SSE-S3 over SSE-KMS**: chosen to keep the project genuinely free (KMS customer-managed keys cost ~$1/month), while still being fully encrypted at rest.
- **On-demand DynamoDB billing**: avoids provisioning/guessing capacity for a low-traffic demo.
- **Prefix-scoped lifecycle rules**: S3 lifecycle rules are limited to one prefix each in the current console UI, so four rules (one per hospital/type combination) implement what could conceptually be described as two policies (blocks, slides).
- **CORS set to `*`** on the API for simplicity; a production system would restrict this to the frontend's actual origin.
- **S3 folder placeholder objects**: initially created manually during the console build; codified as `aws_s3_object` resources in Terraform to keep the rebuild fully reproducible rather than relying on a manual step.

## Possible future improvements

- Custom domain + HTTPS for the frontend (currently served over the default S3 website endpoint)
- A `GET /samples?hospital=QEH` list endpoint using the GSI, rather than lookup-by-ID only
- API authentication (currently open, appropriate for a public demo of synthetic data only)
- CloudWatch dashboards / alarms beyond the SNS retention alert

## Repository structure

```
nhs-sample-archive/
  terraform/        Infrastructure as code (all AWS resources)
  lambda/            Python source for the three Lambda functions
    ingest/
    query/
    retention/
  frontend/          Static lookup page (index.html)
  retention-checker/ Self-hosted retention checker (Docker, cron, CI/CD)
    retention_checker.py
    Dockerfile
    requirements.txt
    run.sh
  .github/
    workflows/
      docker-build.yml
  docs/
    architecture-diagram.png
    images/
      manual-build/     Screenshots from the manual console build
      terraform-build/  Screenshots from the Terraform build
```

## Running this yourself

```
cd terraform
terraform init
terraform apply    # prompts for an alert email, or set it in terraform.tfvars
```

Outputs include the API URL and frontend website URL. Tear down with `terraform destroy`.

To run the self-hosted retention checker:

```
cd retention-checker
docker build -t retention-checker:latest .
docker run --rm -e BUCKET_NAME="<your-bucket-name>" -e AWS_REGION="eu-west-2" -v ~/.aws:/root/.aws:ro retention-checker:latest
```

## Tech stack

AWS: S3, DynamoDB, Lambda, API Gateway (HTTP API), EventBridge Scheduler, SNS, CloudTrail, IAM
IaC: Terraform
Containers/CI: Docker, GitHub Actions
Systems: Linux (Ubuntu), Bash, cron
Language: Python 3.13 (Lambda), Python 3.12 (retention checker), vanilla HTML/CSS/JS (frontend)
