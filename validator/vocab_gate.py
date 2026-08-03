from __future__ import annotations

from dataclasses import dataclass

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

EXEMPT_NAMESPACES: tuple[str, ...] = (
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "http://www.w3.org/2000/01/rdf-schema#",
    "http://www.w3.org/2002/07/owl#",
    "http://www.w3.org/2001/XMLSchema#",
    "http://www.w3.org/ns/shacl#",
)


@dataclass(frozen=True)
class VocabViolation:
    term: str
    term_kind: str  # "class" | "property"
    message: str


def _is_exempt(iri: str) -> bool:
    return any(iri.startswith(prefix) for prefix in EXEMPT_NAMESPACES)


def _is_policed(iri: str, policed_namespaces: tuple[str, ...]) -> bool:
    if _is_exempt(iri) or not policed_namespaces:
        return False
    return any(iri.startswith(ns) for ns in policed_namespaces)


def _declared_terms(ontology: Graph) -> tuple[set[str], set[str]]:
    classes: set[str] = set()
    properties: set[str] = set()

    for subject in ontology.subjects(RDF.type, OWL.Class):
        classes.add(str(subject))
    for subject in ontology.subjects(RDF.type, RDFS.Class):
        classes.add(str(subject))

    for subject in ontology.subjects(RDF.type, OWL.ObjectProperty):
        properties.add(str(subject))
    for subject in ontology.subjects(RDF.type, OWL.DatatypeProperty):
        properties.add(str(subject))
    for subject in ontology.subjects(RDF.type, RDF.Property):
        properties.add(str(subject))

    return classes, properties


def check_vocabulary(
    data: Graph,
    ontology: Graph,
    policed_namespaces: tuple[str, ...],
) -> list[VocabViolation]:
    """Closed-world gate: policed-namespace terms must be declared in the ontology."""
    declared_classes, declared_properties = _declared_terms(ontology)
    violations: list[VocabViolation] = []
    seen: set[tuple[str, str]] = set()

    def add_violation(term: str, term_kind: str) -> None:
        key = (term, term_kind)
        if key in seen:
            return
        seen.add(key)
        violations.append(
            VocabViolation(
                term=term,
                term_kind=term_kind,
                message=f"Undeclared {term_kind} in policed namespace: {term}",
            )
        )

    for _subject, predicate, obj in data:
        pred = str(predicate)
        if _is_policed(pred, policed_namespaces) and pred not in declared_properties:
            add_violation(pred, "property")

        if predicate == RDF.type and isinstance(obj, URIRef):
            cls = str(obj)
            if _is_policed(cls, policed_namespaces) and cls not in declared_classes:
                add_violation(cls, "class")

    return violations
