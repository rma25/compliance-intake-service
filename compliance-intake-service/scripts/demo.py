"""End-to-end demo without a running server. Run: python -m scripts.demo

Exercises the service layer directly across a few representative cases.
"""

from __future__ import annotations

from app.dependencies import get_service
from app.models import Party, ScreeningRequest, TransactionType

service = get_service()

CASES = [
    ("Clean home buyer", Party(name="Jane Doe", country="US"), 450_000, TransactionType.HOME),
    ("High-value hotel", Party(name="John Smith", country="US"), 8_500_000, TransactionType.HOTEL),
    ("Sanctioned party", Party(name="Ivan Sokolov", country="US"), 1_000, TransactionType.HOME),
    (
        "PEP + timeshare",
        Party(name="Robert King", country="US"),
        120_000,
        TransactionType.TIMESHARE,
    ),
    ("High-risk country", Party(name="Olga Petrova", country="RU"), 600_000, TransactionType.HOME),
]


def main() -> None:
    for label, party, amount, txn in CASES:
        req = ScreeningRequest(party=party, amount=amount, transaction_type=txn)
        resp = service.process_intake(
            req, document=b"%PDF demo", document_filename="id.pdf", content_type="application/pdf"
        )
        print(f"\n{label}: {resp.decision.value.upper()}  (risk score {resp.risk_score})")
        for reason in resp.reasons:
            print(f"  - {reason}")
        print(f"  audit_id={resp.audit_id}")


if __name__ == "__main__":
    main()
