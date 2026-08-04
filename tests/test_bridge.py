"""Tests for OntoHarness GapForge bridge."""
from fastapi.testclient import TestClient

from api.app.main import app

client = TestClient(app)


def test_bridge_gap_record_projects_and_validates():
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/bridge/gap-record",
            json={
                "domain": "biomedical",
                "record": {
                    "id": "gap-demo",
                    "claim": "Endpoint sensitivity may have been insufficient.",
                    "confidence": 0.62,
                    "gap_class": "endpoint",
                    "genes": [{"id": "ENSG1", "symbol": "BRCA1"}],
                    "disease": {"id": "MONDO:1", "name": "Alzheimer disease"},
                },
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["validation"]["conforms"] is True
    assert "bio:Hypothesis" in body["turtle"]
    assert "bio:supports" in body["turtle"]


def test_bridge_gap_record_catches_fabricated_predicate():
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/bridge/gap-record",
            json={
                "domain": "biomedical",
                "run_validation": False,
                "record": {
                    "id": "gap-bad",
                    "claim": "Bad agent output",
                    "confidence": 0.5,
                },
            },
        )
    assert r.status_code == 200
    # Manual validate via validate endpoint with fabricated content
    bad_turtle = """
@prefix bio: <https://ontoharness.dev/biomedical#> .
bio:g1 a bio:Gene ;
    bio:hasTherapeuticTarget bio:d1 .
bio:d1 a bio:Disease .
"""
    with TestClient(app) as c:
        v = c.post(
            "/api/v1/validate",
            json={"domain": "biomedical", "format": "turtle", "content": bad_turtle},
        )
    assert v.json()["conforms"] is False
