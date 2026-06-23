from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_screen_endpoint_clear():
    r = client.post(
        "/screen",
        json={"party": {"name": "Jane Doe", "country": "US"}, "amount": 100000},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "clear"


def test_screen_endpoint_block_on_sanctions():
    r = client.post("/screen", json={"party": {"name": "Ivan Sokolov"}, "amount": 100})
    assert r.status_code == 200
    assert r.json()["decision"] == "block"


def test_intake_with_file_review():
    r = client.post(
        "/intake",
        data={
            "party_name": "Robert King",  # PEP
            "country": "US",
            "amount": "5000000",  # high value
            "transaction_type": "hotel",
        },
        files={"document": ("id.pdf", b"%PDF fake", "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "review"
    assert body["document_uri"]
