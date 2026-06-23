"""Shared pytest fixtures. `tmp_path` is a built-in per-test temp directory."""

from __future__ import annotations

import pytest

from app.audit import JsonlAuditSink
from app.screening import ScreeningEngine
from app.service import IntakeService
from app.storage import LocalDocumentStore

WATCHLIST = [
    {"name": "Ivan Sokolov", "category": "sanctions", "list_name": "OFAC SDN (mock)"},
    {"name": "Robert King", "category": "pep", "list_name": "PEP (mock)"},
]


@pytest.fixture
def engine() -> ScreeningEngine:
    return ScreeningEngine(
        watchlist=WATCHLIST,
        review_threshold=3_000_000,
        blocked_countries={"IR", "KP"},
        high_risk_countries={"RU"},
    )


@pytest.fixture
def service(engine, tmp_path) -> IntakeService:
    store = LocalDocumentStore(tmp_path / "docs")
    audit = JsonlAuditSink(tmp_path / "audit.jsonl")
    return IntakeService(engine=engine, store=store, audit=audit)
