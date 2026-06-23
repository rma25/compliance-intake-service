"""Composition root: build and wire the service from settings (FastAPI DI)."""

from __future__ import annotations

from functools import lru_cache

from .audit import AuditSink, JsonlAuditSink
from .config import Settings, get_settings
from .screening import ScreeningEngine
from .service import IntakeService
from .storage import DocumentStore, LocalDocumentStore


def _build_store(s: Settings) -> DocumentStore:
    if s.storage_backend == "s3":
        from .storage import S3DocumentStore

        return S3DocumentStore(bucket=s.s3_bucket, region=s.aws_region)
    return LocalDocumentStore(s.documents_dir)


def _build_audit(s: Settings) -> AuditSink:
    if s.audit_backend == "dynamodb":
        from .audit import DynamoDbAuditSink

        return DynamoDbAuditSink(table_name=s.dynamodb_table, region=s.aws_region)
    return JsonlAuditSink(s.audit_log_path)


@lru_cache
def get_service() -> IntakeService:
    s = get_settings()
    engine = ScreeningEngine.from_file(
        s.watchlist_path,
        review_threshold=s.review_threshold,
        blocked_countries=set(s.blocked_countries),
        high_risk_countries=set(s.high_risk_countries),
    )
    return IntakeService(engine=engine, store=_build_store(s), audit=_build_audit(s))
