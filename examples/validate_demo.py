#!/usr/bin/env python3
"""
End-to-end OntoHarness validation demo — no GapForge or Neo4j required.

Run (from repo root, with API on :8010):
    .venv\\Scripts\\python examples/validate_demo.py
    .venv\\Scripts\\python examples/validate_demo.py --base-url http://localhost:8010
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

VALID_TURTLE = """
@prefix bio: <https://ontoharness.dev/biomedical#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

bio:gene1 a bio:Gene ;
    bio:hasSymbol "BRCA1" ;
    bio:associatedWith bio:disease1 ;
    bio:hasScore "0.92"^^<http://www.w3.org/2001/XMLSchema#decimal> .

bio:disease1 a bio:Disease ;
    bio:hasIdentifier "MONDO:0007254" .
"""

# LLM-style hallucination: plausible predicate, not declared in ontology.ttl
FABRICATED_TURTLE = """
@prefix bio: <https://ontoharness.dev/biomedical#> .

bio:gene1 a bio:Gene ;
    bio:hasTherapeuticTarget bio:disease1 .

bio:disease1 a bio:Disease .
"""


def post_validate(base_url: str, content: str) -> dict:
    payload = json.dumps(
        {"domain": "biomedical", "format": "turtle", "content": content.strip()}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/v1/validate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="OntoHarness validate API demo")
    parser.add_argument("--base-url", default="http://localhost:8010")
    args = parser.parse_args()

    try:
        print(f"=== OntoHarness demo ({args.base_url}) ===\n")

        print("1) Valid gene–disease association (should conform)")
        ok = post_validate(args.base_url, VALID_TURTLE)
        print(f"   conforms={ok['conforms']}")
        assert ok["conforms"], "expected valid turtle to conform"
        print("   OK\n")

        print("2) Fabricated predicate bio:hasTherapeuticTarget (should fail vocab gate)")
        bad = post_validate(args.base_url, FABRICATED_TURTLE)
        print(f"   conforms={bad['conforms']}")
        print(f"   vocab_violations={json.dumps(bad.get('vocab_violations', []), indent=2)}")
        print(f"   repair_hints={bad.get('repair_hints', [])}")
        assert not bad["conforms"], "expected fabricated predicate to fail"
        assert any(
            "hasTherapeuticTarget" in v.get("term", "") for v in bad.get("vocab_violations", [])
        )
        print("   BLOCKED (this is what GapForge surfaces in the review UI)\n")

        print("3) Score out of range (should fail competency question cq-association-score)")
        bad_score = """
@prefix bio: <https://ontoharness.dev/biomedical#> .
bio:gene1 a bio:Gene ;
    bio:hasSymbol "BRCA1" ;
    bio:associatedWith bio:disease1 ;
    bio:hasScore "1.5"^^<http://www.w3.org/2001/XMLSchema#decimal> .
bio:disease1 a bio:Disease ;
    bio:hasIdentifier "MONDO:0007254" .
"""
        cq = post_validate(args.base_url, bad_score)
        print(f"   conforms={cq['conforms']}")
        print(f"   competency_violations={json.dumps(cq.get('competency_violations', []), indent=2)}")
        assert not cq["conforms"]
        assert any(v.get("cq_id") == "cq-association-score" for v in cq.get("competency_violations", []))
        print("   BLOCKED by competency-question contract\n")

        print("Done — vocab gate + SHACL + competency questions.")
        return 0

    except urllib.error.URLError as exc:
        print(f"Cannot reach OntoHarness at {args.base_url}: {exc}", file=sys.stderr)
        print("Start the sidecar: python -m uvicorn api.app.main:app --port 8010", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
