"""FastAPI application: /health, /screen (JSON), /intake (multipart + file)."""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, File, Form, UploadFile

from .dependencies import get_service
from .models import (
    IntakeResponse,
    Party,
    PartyRole,
    ScreeningRequest,
    ScreeningResult,
    TransactionType,
)
from .service import IntakeService

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("compliance-intake")

app = FastAPI(
    title="Compliance Intake & Screening Service",
    description="Demo KYC / AML intake: store a document, screen the party, write an audit trail.",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/screen", response_model=ScreeningResult)
def screen(req: ScreeningRequest, service: IntakeService = Depends(get_service)) -> ScreeningResult:
    """Screen a party + transaction without storing a document (pure decision)."""
    result = service.screen_only(req)
    log.info("screen party=%s amount=%s -> %s", req.party.name, req.amount, result.decision.value)
    return result


@app.post("/intake", response_model=IntakeResponse)
async def intake(
    party_name: str = Form(...),
    country: str = Form("US"),
    role: PartyRole = Form(PartyRole.BUYER),
    amount: float = Form(...),
    transaction_type: TransactionType = Form(TransactionType.HOME),
    document: UploadFile | None = File(None),
    service: IntakeService = Depends(get_service),
) -> IntakeResponse:
    """Full intake: optional document upload + screening + audit record."""
    req = ScreeningRequest(
        party=Party(name=party_name, country=country, role=role),
        amount=amount,
        transaction_type=transaction_type,
    )
    doc_bytes = await document.read() if document is not None else None
    response = service.process_intake(
        req,
        document=doc_bytes,
        document_filename=document.filename if document else None,
        content_type=(
            (document.content_type or "application/octet-stream")
            if document
            else "application/octet-stream"
        ),
    )
    log.info(
        "intake party=%s -> %s (audit %s)", party_name, response.decision.value, response.audit_id
    )
    return response
