from app.models import Decision, Party, ScreeningRequest, TransactionType


def _req(name="Jane Doe", country="US", amount=500_000, txn=TransactionType.HOME):
    return ScreeningRequest(
        party=Party(name=name, country=country), amount=amount, transaction_type=txn
    )


def test_clean_party_clears(engine):
    res = engine.screen(_req())
    assert res.decision == Decision.CLEAR
    assert res.risk_score == 0


def test_sanctions_match_blocks(engine):
    res = engine.screen(_req(name="Ivan Sokolov"))
    assert res.decision == Decision.BLOCK
    assert res.hits and res.hits[0].category == "sanctions"


def test_pep_match_reviews(engine):
    res = engine.screen(_req(name="Robert King"))
    assert res.decision == Decision.REVIEW


def test_match_is_case_and_space_insensitive(engine):
    res = engine.screen(_req(name="  ivan   SOKOLOV "))
    assert res.decision == Decision.BLOCK


def test_high_value_triggers_review(engine):
    res = engine.screen(_req(amount=5_000_000))
    assert res.decision == Decision.REVIEW


def test_blocked_country_blocks(engine):
    res = engine.screen(_req(country="IR"))
    assert res.decision == Decision.BLOCK


def test_high_risk_country_reviews(engine):
    res = engine.screen(_req(country="RU"))
    assert res.decision == Decision.REVIEW


def test_most_severe_decision_wins(engine):
    # sanctions (block) + high value (review) -> block
    res = engine.screen(_req(name="Ivan Sokolov", amount=9_000_000))
    assert res.decision == Decision.BLOCK


def test_elevated_asset_category_adds_risk(engine):
    home = engine.screen(_req(txn=TransactionType.HOME))
    hotel = engine.screen(_req(txn=TransactionType.HOTEL))
    assert hotel.risk_score > home.risk_score
