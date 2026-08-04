"""Project GapForge gap records to biomedical Turtle (OntoHarness bridge)."""
from __future__ import annotations

from xml.sax.saxutils import escape

XSD_DECIMAL = "<http://www.w3.org/2001/XMLSchema#decimal>"
XSD_DATETIME = "<http://www.w3.org/2001/XMLSchema#dateTime>"


def _lit(value: str) -> str:
    return f'"{escape(value)}"'


def _dec(value: float) -> str:
    return f'"{value}"^^{XSD_DECIMAL}'


def _safe_local(raw: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)
    return cleaned.strip("-") or "item"


def gap_record_to_turtle(record: dict) -> str:
    """
    GapForge-shaped JSON → Turtle.

    Expected keys: id, claim, confidence, gap_class?, genes?, disease?,
    approved_at?, provenance_hash?
    genes: [{id, symbol}]
    disease: {id, name}
    """
    gap_id = record.get("id") or "gap-unknown"
    claim = record.get("claim") or ""
    confidence = float(record.get("confidence") or 0)
    genes = record.get("genes") or []
    disease = record.get("disease")

    hyp_local = _safe_local(gap_id)
    hyp_lines = [
        f"bio:{hyp_local} a bio:Hypothesis ;",
        f"    rdfs:label {_lit(claim)} ;",
        f"    bio:confidence {_dec(max(0.0, min(1.0, confidence)))} ;",
    ]
    gap_class = record.get("gap_class")
    if gap_class:
        hyp_lines.append(f"    bio:gapClass {_lit(str(gap_class))} ;")
    approved_at = record.get("approved_at")
    if approved_at:
        hyp_lines.append(f'    bio:approvedAt "{escape(str(approved_at))}"^^{XSD_DATETIME} ;')
    provenance_hash = record.get("provenance_hash")
    if provenance_hash:
        hyp_lines.append(f"    bio:provenanceHash {_lit(str(provenance_hash))} ;")
    hyp_lines[-1] = hyp_lines[-1].rstrip(" ;") + " ."

    lines = [
        "@prefix bio: <https://ontoharness.dev/biomedical#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
        *hyp_lines,
    ]

    score = max(0.0, min(1.0, confidence))
    disease_local = _safe_local(disease["id"]) if disease and disease.get("id") else "disease-unknown"

    if disease and disease.get("id"):
        disease_lines = [
            "",
            f"bio:{disease_local} a bio:Disease ;",
            f"    bio:hasIdentifier {_lit(disease['id'])}",
        ]
        if disease.get("name"):
            disease_lines[-1] += " ;"
            disease_lines.append(f"    rdfs:label {_lit(disease['name'])} .")
        else:
            disease_lines[-1] += " ."
        lines.extend(disease_lines)

    for gene in genes:
        gid = gene.get("id") or gene.get("symbol") or "gene-unknown"
        symbol = gene.get("symbol") or gid
        glocal = _safe_local(gid)
        lines.extend(
            [
                "",
                f"bio:{glocal} a bio:Gene ;",
                f"    bio:hasSymbol {_lit(symbol)} ;",
                f"    bio:supports bio:{hyp_local} ;",
                f"    bio:associatedWith bio:{disease_local} ;",
                f'    bio:hasScore "{score}"^^{XSD_DECIMAL} .',
            ]
        )

    return "\n".join(lines) + "\n"
