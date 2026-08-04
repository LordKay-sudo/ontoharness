from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request

from bridge.gapforge_projector import gap_record_to_turtle
from validator.engine import ValidationEngine

router = APIRouter()


class GapRecordBridgeRequest(BaseModel):
    domain: str = Field(default="biomedical", description="OntoHarness domain bundle")
    record: dict = Field(description="GapForge gap record (id, claim, confidence, genes, disease, …)")
    run_validation: bool = Field(default=True, description="Run vocab gate + SHACL after projection")


class GapRecordBridgeResponse(BaseModel):
    domain: str
    turtle: str
    validation: dict | None = None


@router.post("/bridge/gap-record", response_model=GapRecordBridgeResponse)
def bridge_gap_record(body: GapRecordBridgeRequest, request: Request) -> GapRecordBridgeResponse:
    """Neo4j ↔ RDF bridge: project a GapForge record to Turtle and optionally validate."""
    try:
        turtle = gap_record_to_turtle(body.record)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid gap record: {exc}") from exc

    validation = None
    if body.run_validation:
        bundles = request.app.state.domain_bundles
        bundle = bundles.get(body.domain)
        if bundle is None:
            raise HTTPException(status_code=404, detail=f"Unknown domain: {body.domain}")
        engine = ValidationEngine(bundle)
        result = engine.validate_turtle(turtle)
        validation = result.to_dict()

    return GapRecordBridgeResponse(domain=body.domain, turtle=turtle, validation=validation)
