# Compliance Intake & Screening Service

A small but real **KYC / AML intake service**: it accepts a party + a document, stores the
document, **screens** the party against a (mock) sanctions/PEP watchlist plus jurisdiction and
high-value rules, writes an **audit-trail** record, and returns a structured decision
(`clear` / `review` / `block`).

It runs **locally with zero AWS setup**, and is architected so the storage and audit layers
swap to **AWS S3 + DynamoDB** by changing two environment variables — demonstrating the
**Python + AWS** intersection directly.

> ⚠️ **This is a learning/demo project, not a real compliance system.** Real sanctions/AML
> screening uses fuzzy matching against official OFAC/UN/EU lists, secondary identifiers,
> risk models, and human review. Do not use this to make real compliance decisions.

---

## Why this project exists

It's a deliberate rebuild — in **Python on AWS** — of the kind of work done on a real-estate
transaction platform: identity/KYC checks, secure document handling, and audit trails. That
makes it a strong, authentic portfolio piece for a software role in **Legal & Compliance
technology**: it speaks the domain (AML/KYC, audit, data handling) *and* the stack
(Python, FastAPI, boto3, AWS).

## Architecture at a glance

```
HTTP (FastAPI)  ──►  IntakeService  ──►  ScreeningEngine   (pure rules: watchlist, country, value)
                          │            └► DocumentStore     (Local file  | S3)
                          └──────────────► AuditSink        (JSONL file  | DynamoDB)
```

- **Interfaces over implementations.** `DocumentStore` and `AuditSink` are `typing.Protocol`
  interfaces with a local impl and an AWS impl each. The composition root
  (`app/dependencies.py`) picks the impl from settings — classic dependency injection.
- **The screening engine is pure** (no I/O after construction), so it's trivial to unit-test
  and packages cleanly into a Lambda.

### How it maps to C# / .NET (for orientation)

| This project (Python) | Your C# world |
|---|---|
| Pydantic models (`app/models.py`) | DTOs / records with validation |
| `typing.Protocol` (`DocumentStore`, `AuditSink`) | interfaces |
| `@dataclass(frozen=True)` (`AuditEvent`) | an immutable `record` |
| `pydantic-settings` (`app/config.py`) | the Options pattern (`IOptions<T>`) |
| `app/dependencies.py` | your DI container registration |
| FastAPI routes (`app/main.py`) | ASP.NET Minimal API endpoints |
| pytest (`tests/`) | xUnit / NUnit |
| boto3 | the AWS SDK |

## Project layout

```
compliance-intake-service/
├── app/
│   ├── main.py           # FastAPI app + routes (/health, /screen, /intake)
│   ├── config.py         # settings (env-driven, CIS_ prefix)
│   ├── models.py         # Pydantic DTOs + enums
│   ├── screening.py      # the screening engine (pure rules)
│   ├── storage.py        # DocumentStore: Local + S3
│   ├── audit.py          # AuditSink: JSONL + DynamoDB
│   ├── service.py        # orchestration (store -> screen -> audit)
│   ├── dependencies.py   # composition root / DI
│   └── data/watchlist.json
├── tests/                # pytest: unit + service + API tests
├── scripts/demo.py       # end-to-end demo, no server needed
├── infra/README.md       # the AWS path: Terraform + Lambda notes
├── requirements.txt / requirements-dev.txt
└── pyproject.toml        # black / ruff / mypy config
```

---

## Quickstart

```bash
# 1) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 2) Install (dev deps include pytest/httpx/black/ruff/mypy)
pip install -r requirements-dev.txt

# 3) See it work end-to-end (no server required)
python -m scripts.demo

# 4) Run the test suite
pytest -q

# 5) Run the API
./run.sh                              # or: uvicorn app.main:app --reload
# open http://127.0.0.1:8000/docs  for interactive Swagger UI
```

### Try the API

```bash
# Pure screening decision (JSON)
curl -s -X POST http://127.0.0.1:8000/screen \
  -H "Content-Type: application/json" \
  -d '{"party": {"name": "Ivan Sokolov", "country": "US"}, "amount": 100}' | python -m json.tool

# Full intake with a document upload (multipart)
curl -s -X POST http://127.0.0.1:8000/intake \
  -F "party_name=Robert King" \
  -F "country=US" \
  -F "amount=5000000" \
  -F "transaction_type=hotel" \
  -F "document=@README.md" | python -m json.tool
```

The audit trail is written to `_data/audit_log.jsonl` (one JSON object per line); uploaded
documents land in `_data/documents/`.

---

## Switching to AWS

No code changes — just flip the backends (see `infra/README.md` for Terraform + Lambda):

```bash
export CIS_STORAGE_BACKEND=s3
export CIS_AUDIT_BACKEND=dynamodb
export CIS_S3_BUCKET=my-compliance-docs
export CIS_DYNAMODB_TABLE=compliance-audit
```

`S3DocumentStore` (in `app/storage.py`) and `DynamoDbAuditSink` (in `app/audit.py`) take over,
using `boto3`. They lazy-import boto3, so the local path never needs AWS credentials.

---

## Dev tooling

```bash
black .          # format
ruff check .     # lint
mypy app         # static type check (type hints make this meaningful)
```

## Screening rules (demo)

| Trigger | Effect |
|---|---|
| Sanctions watchlist match | **BLOCK** |
| Comprehensively sanctioned country (IR, KP, SY, CU) | **BLOCK** |
| PEP watchlist match | **REVIEW** |
| High-risk country (RU, VE, MM) | **REVIEW** |
| Amount ≥ $3,000,000 | **REVIEW** (enhanced due diligence) |
| Hotel / timeshare / commercial asset | +risk score |

Most severe outcome wins. All thresholds/lists are configurable via env or `app/config.py`.

---

## Suggested next steps (to deepen it)
- Add **fuzzy name matching** (e.g., `rapidfuzz`) instead of exact match.
- Add a `GET /audit/{intake_id}` endpoint that reads back the trail.
- Add **auth** (an API key dependency) — a natural FastAPI dependency-injection exercise.
- Containerize with a `Dockerfile` and deploy to ECS/Fargate or Lambda.
