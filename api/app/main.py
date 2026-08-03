from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from api.app.routes import domains, health, validate


def _domains_root() -> Path:
    env = os.getenv("ONTOHARNESS_DOMAINS_DIR")
    if env:
        return Path(env).resolve()
    return (Path(__file__).resolve().parents[2] / "domains").resolve()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from validator.domain_loader import load_domains

    app.state.domains_root = _domains_root()
    app.state.domain_bundles = load_domains(app.state.domains_root)
    yield


app = FastAPI(
    title="OntoHarness",
    description="Competency-question contracts for AI agents: propose in natural language, commit only what passes SHACL.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["system"])
app.include_router(domains.router, prefix="/api/v1", tags=["domains"])
app.include_router(validate.router, prefix="/api/v1", tags=["validate"])
