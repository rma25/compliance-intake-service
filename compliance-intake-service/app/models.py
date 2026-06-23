"""Pydantic models (DTOs) + domain enums.

For a C# dev: Pydantic models are DTOs with built-in validation (like a record
plus FluentValidation). `str, Enum` gives you a string-backed enum.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    HOME = "home"
    HOTEL = "hotel"
    TIMESHARE = "timeshare"
    COMMERCIAL = "commercial"


class PartyRole(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"


class Decision(str, Enum):
    CLEAR = "clear"
    REVIEW = "review"
    BLOCK = "block"


class Party(BaseModel):
    name: str = Field(..., min_length=1)
    country: str = Field("US", description="ISO-3166 alpha-2, e.g. US, GB, IR")
    role: PartyRole = PartyRole.BUYER
    date_of_birth: str | None = None


class ScreeningRequest(BaseModel):
    party: Party
    amount: float = Field(..., ge=0, description="Transaction amount in USD")
    transaction_type: TransactionType = TransactionType.HOME


class WatchlistHit(BaseModel):
    list_name: str
    matched_name: str
    category: str  # "sanctions" | "pep"


class ScreeningResult(BaseModel):
    decision: Decision
    risk_score: int
    reasons: list[str]
    hits: list[WatchlistHit] = []


class IntakeResponse(BaseModel):
    intake_id: str
    decision: Decision
    risk_score: int
    reasons: list[str]
    hits: list[WatchlistHit] = []
    document_uri: str | None = None
    audit_id: str
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
