import pytest
from fastapi.testclient import TestClient

from api.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


VALID_TURTLE = """
@prefix bio: <https://ontoharness.dev/biomedical#> .
bio:gene1 a bio:Gene ;
    bio:hasSymbol "BRCA1" ;
    bio:associatedWith bio:disease1 ;
    bio:hasScore "0.5"^^<http://www.w3.org/2001/XMLSchema#decimal> .
bio:disease1 a bio:Disease ;
    bio:hasIdentifier "MONDO:1" .
"""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_domains(client):
    response = client.get("/api/v1/domains")
    assert response.status_code == 200
    names = [d["name"] for d in response.json()["domains"]]
    assert "biomedical" in names


def test_validate_valid_payload(client):
    response = client.post(
        "/api/v1/validate",
        json={"domain": "biomedical", "content": VALID_TURTLE, "format": "turtle"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["conforms"] is True


def test_validate_fabricated_predicate(client):
    bad = """
    @prefix bio: <https://ontoharness.dev/biomedical#> .
    bio:gene1 a bio:Gene ;
        bio:totallyMadeUp bio:disease1 .
    bio:disease1 a bio:Disease .
    """
    response = client.post(
        "/api/v1/validate",
        json={"domain": "biomedical", "content": bad, "format": "turtle"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["conforms"] is False
    assert body["vocab_violations"]
