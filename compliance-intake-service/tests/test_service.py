import json

from app.models import Party, ScreeningRequest


def test_process_intake_stores_doc_and_audits(service, tmp_path):
    req = ScreeningRequest(party=Party(name="Jane Doe", country="US"), amount=250_000)
    resp = service.process_intake(
        req,
        document=b"%PDF-1.4 fake-bytes",
        document_filename="id.pdf",
        content_type="application/pdf",
    )
    assert resp.document_uri is not None
    assert resp.document_uri.startswith("file://")
    assert resp.audit_id

    audit_file = tmp_path / "audit.jsonl"
    lines = audit_file.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["party_name"] == "Jane Doe"
    assert record["action"] == "intake"


def test_process_intake_without_document_blocks_sanctioned(service):
    req = ScreeningRequest(party=Party(name="Ivan Sokolov", country="US"), amount=100)
    resp = service.process_intake(req)
    assert resp.document_uri is None
    assert resp.decision.value == "block"
