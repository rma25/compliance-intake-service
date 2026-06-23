# Infra notes — the AWS path

The app runs locally with **no AWS** by default (`local` + `jsonl` backends).
To run it "for real" on AWS, flip the backends and point them at real resources:

```bash
export CIS_STORAGE_BACKEND=s3
export CIS_AUDIT_BACKEND=dynamodb
export CIS_S3_BUCKET=my-compliance-docs
export CIS_DYNAMODB_TABLE=compliance-audit
export CIS_AWS_REGION=us-east-1
```

`app/storage.py::S3DocumentStore` and `app/audit.py::DynamoDbAuditSink` already
implement the `boto3` calls. No app code changes are needed — the composition
root (`app/dependencies.py`) selects them from settings.

## Minimal Terraform starter (S3 + DynamoDB)

```hcl
provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "docs" {
  bucket = "my-compliance-docs"
}

resource "aws_s3_bucket_public_access_block" "docs" {
  bucket                  = aws_s3_bucket.docs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "audit" {
  name         = "compliance-audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "audit_id"

  attribute {
    name = "audit_id"
    type = "S"
  }
}
```

## Running the screener as a Lambda

The screening logic in `app/screening.py` is pure and dependency-free, so it
packages cleanly into a Lambda handler. Sketch:

```python
# lambda_handler.py
from app.screening import ScreeningEngine
from app.models import ScreeningRequest

engine = ScreeningEngine.from_file("app/data/watchlist.json",
    review_threshold=3_000_000, blocked_countries={"IR","KP"}, high_risk_countries={"RU"})

def handler(event, context):
    req = ScreeningRequest(**event)
    return engine.screen(req).model_dump()
```

Package `app/` + deps into a zip (or container image) and deploy. Front it with
API Gateway, or keep FastAPI and deploy the whole app via AWS Lambda Web Adapter
or a small ECS/Fargate service.
