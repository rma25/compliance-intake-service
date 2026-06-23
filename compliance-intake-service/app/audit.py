"""Audit trail: an append-only event log with a local (JSONL) and a DynamoDB sink.

For a C# dev: `@dataclass(frozen=True)` is basically an immutable record.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class AuditEvent:
    actor: str
    action: str
    party_name: str
    party_country: str
    amount: float
    decision: str
    reasons: list[str]
    document_uri: str | None = None
    request_id: str | None = None
    audit_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditSink(Protocol):
    def record(self, event: AuditEvent) -> str: ...


class JsonlAuditSink:
    """Append-only JSON Lines file — a simple, ordered, tamper-evident-ish trail."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: AuditEvent) -> str:
        with self._path.open("a", encoding="utf-8") as f:  # "a" = append-only
            f.write(json.dumps(asdict(event)) + "\n")
        return event.audit_id


class DynamoDbAuditSink:
    """AWS-backed audit sink. Lazy-imports boto3."""

    def __init__(self, table_name: str, region: str = "us-east-1") -> None:
        import boto3

        self._table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def record(self, event: AuditEvent) -> str:
        item = asdict(event)
        item["amount"] = str(item["amount"])  # DynamoDB has no float type
        self._table.put_item(Item=item)
        return event.audit_id
