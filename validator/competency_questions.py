"""Evaluate domain competency questions (SPARQL) against proposed RDF graphs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from rdflib import Graph, URIRef
from rdflib.namespace import RDF

_ASK_PATTERN = re.compile(r"\bASK\b", re.IGNORECASE)
_SELECT_PATTERN = re.compile(r"\bSELECT\b", re.IGNORECASE)
_PREFIX_PATTERN = re.compile(r"PREFIX\s+(\w+):\s+<([^>]+)>", re.IGNORECASE)
_TYPE_PATTERN = re.compile(r"(\?\w+)\s+a\s+(\w+):(\w+)")


@dataclass(frozen=True)
class CompetencyViolation:
    cq_id: str
    question: str
    message: str


def _parse_prefixes(sparql: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _PREFIX_PATTERN.finditer(sparql)}


def _first_select_var(sparql: str) -> str | None:
    match = re.search(r"SELECT\s+(?:DISTINCT\s+)?(\?\w+)", sparql, re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else None


def _primary_type_constraint(sparql: str) -> tuple[str, URIRef] | None:
    """Return (?var_name, type_uri) from the first `?x a prefix:Local` in the CQ."""
    match = _TYPE_PATTERN.search(sparql)
    if not match:
        return None
    var, prefix, local = match.group(1), match.group(2), match.group(3)
    prefixes = _parse_prefixes(sparql)
    ns = prefixes.get(prefix)
    if not ns:
        return None
    return var, URIRef(f"{ns}{local}")


def _ask_result(data: Graph, sparql: str) -> bool:
    rows = list(data.query(sparql))
    if not rows:
        return False
    row = rows[0]
    if isinstance(row, bool):
        return row
    return bool(row[0])


def _select_bindings(data: Graph, sparql: str, var_name: str) -> set[URIRef]:
    rows = list(data.query(sparql))
    if not rows:
        return set()
    idx = 0
    if rows[0].labels:
        try:
            idx = list(rows[0].labels).index(var_name.lstrip("?"))
        except ValueError:
            idx = 0
    return {row[idx] for row in rows if row[idx] is not None}


def _subjects_of_type(data: Graph, type_uri: URIRef) -> set[URIRef]:
    return {s for s in data.subjects(RDF.type, type_uri) if isinstance(s, URIRef)}


def _evaluate_cq(data: Graph, cq: dict[str, Any]) -> CompetencyViolation | None:
    cq_id = str(cq.get("id", "unknown"))
    question = str(cq.get("question", ""))
    sparql = cq.get("sparql")
    if not sparql or not str(sparql).strip():
        return None

    sparql_text = str(sparql).strip()

    if _ASK_PATTERN.search(sparql_text):
        if _ask_result(data, sparql_text):
            return None
        return CompetencyViolation(
            cq_id=cq_id,
            question=question,
            message="ASK competency question returned false.",
        )

    if _SELECT_PATTERN.search(sparql_text):
        var = _first_select_var(sparql_text)
        type_constraint = _primary_type_constraint(sparql_text)
        if not var or not type_constraint:
            return None

        _, type_uri = type_constraint
        conforming = _select_bindings(data, sparql_text, var)
        subjects = _subjects_of_type(data, type_uri)
        missing = subjects - conforming
        if not missing:
            return None
        sample = ", ".join(str(s) for s in list(missing)[:3])
        suffix = "…" if len(missing) > 3 else ""
        return CompetencyViolation(
            cq_id=cq_id,
            question=question,
            message=(
                f"{len(missing)} resource(s) of type {type_uri} do not satisfy the competency "
                f"pattern (e.g. {sample}{suffix})."
            ),
        )

    return None


def check_competency_questions(
    data: Graph,
    competency_questions: tuple[dict[str, Any], ...],
    *,
    required_only: bool = True,
) -> list[CompetencyViolation]:
    violations: list[CompetencyViolation] = []
    for cq in competency_questions:
        if required_only and not cq.get("required_for_commit", False):
            continue
        if cq.get("note") and not cq.get("sparql"):
            continue
        violation = _evaluate_cq(data, cq)
        if violation is not None:
            violations.append(violation)
    return violations
