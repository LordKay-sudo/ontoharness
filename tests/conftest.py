from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ROOT / "domains"


@pytest.fixture(scope="session")
def biomedical_domain():
    from validator.domain_loader import load_domain

    return load_domain(DOMAINS / "biomedical")
