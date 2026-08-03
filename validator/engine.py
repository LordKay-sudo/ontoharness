from __future__ import annotations

from dataclasses import dataclass, field

from rdflib import Graph

from validator.domain_loader import DomainBundle
from validator.repair import build_repair_hints
from validator.shacl_validator import ShaclViolation, check_shacl
from validator.vocab_gate import VocabViolation, check_vocabulary


@dataclass
class ValidationResult:
    domain: str
    conforms: bool
    vocab_violations: list[VocabViolation] = field(default_factory=list)
    shacl_violations: list[ShaclViolation] = field(default_factory=list)
    repair_hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "conforms": self.conforms,
            "vocab_violations": [
                {"term": v.term, "term_kind": v.term_kind, "message": v.message}
                for v in self.vocab_violations
            ],
            "shacl_violations": [
                {
                    "message": v.message,
                    "path": v.path,
                    "focus_node": v.focus_node,
                    "source_shape": v.source_shape,
                }
                for v in self.shacl_violations
            ],
            "repair_hints": self.repair_hints,
        }


class ValidationEngine:
    def __init__(self, domain: DomainBundle) -> None:
        self._domain = domain

    @property
    def domain(self) -> DomainBundle:
        return self._domain

    def validate_graph(self, data: Graph) -> ValidationResult:
        vocab_violations = check_vocabulary(
            data,
            self._domain.ontology_graph,
            self._domain.policed_namespaces,
        )
        shacl_ok, shacl_violations = check_shacl(
            data,
            self._domain.ontology_graph,
            self._domain.shapes_graph,
        )

        conforms = not vocab_violations and shacl_ok
        repair_hints = build_repair_hints(vocab_violations, shacl_violations)

        return ValidationResult(
            domain=self._domain.name,
            conforms=conforms,
            vocab_violations=vocab_violations,
            shacl_violations=shacl_violations,
            repair_hints=repair_hints,
        )

    def validate_turtle(self, turtle: str) -> ValidationResult:
        data = Graph()
        data.parse(data=turtle, format="turtle")
        return self.validate_graph(data)
