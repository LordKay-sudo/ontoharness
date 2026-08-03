from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/domains")
def list_domains(request: Request) -> dict:
    bundles = request.app.state.domain_bundles
    return {
        "domains": [
            {
                "name": b.name,
                "label": b.label,
                "description": b.description.strip(),
                "policed_namespaces": list(b.policed_namespaces),
                "competency_question_count": len(b.competency_questions),
            }
            for b in bundles.values()
        ]
    }


@router.get("/domains/{domain_name}")
def get_domain(domain_name: str, request: Request) -> dict:
    bundles = request.app.state.domain_bundles
    bundle = bundles.get(domain_name)
    if bundle is None:
        raise HTTPException(status_code=404, detail=f"Unknown domain: {domain_name}")
    return {
        "name": bundle.name,
        "label": bundle.label,
        "description": bundle.description.strip(),
        "policed_namespaces": list(bundle.policed_namespaces),
        "competency_questions": bundle.competency_questions,
    }
