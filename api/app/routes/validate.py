from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from validator.engine import ValidationEngine

router = APIRouter()


class ValidateRequest(BaseModel):
    domain: str = Field(default="biomedical", description="Registered domain name")
    content: str = Field(description="RDF payload (Turtle by default)")
    format: Literal["turtle", "nt", "xml"] = "turtle"


@router.post("/validate")
def validate_payload(body: ValidateRequest, request: Request) -> dict:
    bundles = request.app.state.domain_bundles
    bundle = bundles.get(body.domain)
    if bundle is None:
        raise HTTPException(status_code=404, detail=f"Unknown domain: {body.domain}")

    engine = ValidationEngine(bundle)
    try:
        if body.format == "turtle":
            result = engine.validate_turtle(body.content)
        else:
            from rdflib import Graph

            graph = Graph()
            graph.parse(data=body.content, format=body.format)
            result = engine.validate_graph(graph)
    except Exception as exc:  # noqa: BLE001 — surface parse errors to client
        raise HTTPException(status_code=400, detail=f"RDF parse error: {exc}") from exc

    return result.to_dict()
