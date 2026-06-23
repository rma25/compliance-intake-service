"""Orchestration / business layer: store document -> screen -> audit -> respond."""

from __future__ import annotations

from uuid import uuid4

from .audit import AuditEvent, AuditSink
from .models import IntakeResponse, ScreeningRequest, ScreeningResult
from .screening import ScreeningEngine
from .storage import DocumentStore


class IntakeService:
    def __init__(self, engine: ScreeningEngine, store: DocumentStore, audit: AuditSink) -> None:
        # Dependencies injected via the constructor (testable; swap impls freely).
        self._engine = engine
        self._store = store
        self._audit = audit

    def screen_only(self, req: ScreeningRequest) -> ScreeningResult:
        return self._engine.screen(req)

    def process_intake(
        self,
        req: ScreeningRequest,
        *,
        document: bytes | None = None,
        document_filename: str | None = None,
        content_type: str = "application/octet-stream",
        actor: str = "api",
    ) -> IntakeResponse:
        intake_id = str(uuid4())

        document_uri: str | None = None
        if document is not None and document_filename:
            key = f"{intake_id}/{document_filename}"
            document_uri = self._store.save(key, document, content_type)

        result = self._engine.screen(req)

        event = AuditEvent(
            actor=actor,
            action="intake",
            party_name=req.party.name,
            party_country=req.party.country,
            amount=req.amount,
            decision=result.decision.value,
            reasons=result.reasons,
            document_uri=document_uri,
            request_id=intake_id,
        )
        audit_id = self._audit.record(event)

        return IntakeResponse(
            intake_id=intake_id,
            decision=result.decision,
            risk_score=result.risk_score,
            reasons=result.reasons,
            hits=result.hits,
            document_uri=document_uri,
            audit_id=audit_id,
        )
