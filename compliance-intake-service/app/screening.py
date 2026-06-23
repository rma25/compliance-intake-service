"""Deterministic screening engine: watchlist + jurisdiction + high-value rules.

Pure logic, no I/O after construction, so it is trivially unit-testable.

NOTE: This is a DEMO. Real sanctions/AML screening uses fuzzy matching against
official OFAC/UN/EU lists, secondary identifiers (DOB, address), risk models,
and human review. Do not use this as-is for real compliance decisions.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    Decision,
    ScreeningRequest,
    ScreeningResult,
    TransactionType,
    WatchlistHit,
)


def _normalize(name: str) -> str:
    """Lowercase + collapse whitespace, for case/spacing-insensitive matching."""
    return " ".join(name.lower().strip().split())


_SEVERITY = {Decision.CLEAR: 0, Decision.REVIEW: 1, Decision.BLOCK: 2}


def _escalate(current: Decision, candidate: Decision) -> Decision:
    """Return the more severe of two decisions (most severe wins)."""
    return current if _SEVERITY[current] >= _SEVERITY[candidate] else candidate


class ScreeningEngine:
    def __init__(
        self,
        watchlist: list[dict],
        review_threshold: float,
        blocked_countries: set[str],
        high_risk_countries: set[str],
    ) -> None:
        # Index by normalized name -> entry for O(1) exact-match lookups.
        self._index = {_normalize(e["name"]): e for e in watchlist}
        self._review_threshold = review_threshold
        self._blocked = {c.upper() for c in blocked_countries}
        self._high_risk = {c.upper() for c in high_risk_countries}

    @classmethod
    def from_file(cls, path: str | Path, **kwargs) -> ScreeningEngine:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(watchlist=data, **kwargs)

    def screen(self, req: ScreeningRequest) -> ScreeningResult:
        reasons: list[str] = []
        hits: list[WatchlistHit] = []
        score = 0
        decision = Decision.CLEAR

        party = req.party
        country = party.country.upper()

        # 1) Watchlist (sanctions / PEP) — exact normalized-name match.
        entry = self._index.get(_normalize(party.name))
        if entry is not None:
            hit = WatchlistHit(
                list_name=entry.get("list_name", "watchlist"),
                matched_name=entry["name"],
                category=entry.get("category", "sanctions"),
            )
            hits.append(hit)
            if hit.category == "sanctions":
                score += 100
                reasons.append(f"Sanctions match: {hit.matched_name} ({hit.list_name})")
                decision = Decision.BLOCK
            else:  # pep
                score += 40
                reasons.append(f"PEP match: {hit.matched_name} ({hit.list_name})")
                decision = _escalate(decision, Decision.REVIEW)

        # 2) Comprehensively sanctioned jurisdiction -> block.
        if country in self._blocked:
            score += 100
            reasons.append(f"Comprehensively sanctioned jurisdiction ({country})")
            decision = Decision.BLOCK
        # 3) High-risk jurisdiction -> review.
        elif country in self._high_risk:
            score += 30
            reasons.append(f"High-risk jurisdiction ({country})")
            decision = _escalate(decision, Decision.REVIEW)

        # 4) High-value transaction -> enhanced due diligence (review).
        if req.amount >= self._review_threshold:
            score += 25
            reasons.append(
                f"High-value transaction ${req.amount:,.0f} >= "
                f"${self._review_threshold:,.0f} threshold (enhanced due diligence)"
            )
            decision = _escalate(decision, Decision.REVIEW)

        # 5) Asset-category risk (hotels/timeshares/commercial are higher-risk vehicles).
        elevated = {TransactionType.HOTEL, TransactionType.TIMESHARE, TransactionType.COMMERCIAL}
        if req.transaction_type in elevated:
            score += 10
            reasons.append(f"Elevated-risk asset category: {req.transaction_type.value}")

        if not reasons:
            reasons.append("No risk factors triggered")

        return ScreeningResult(decision=decision, risk_score=score, reasons=reasons, hits=hits)
