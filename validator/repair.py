from __future__ import annotations

from validator.shacl_validator import ShaclViolation
from validator.vocab_gate import VocabViolation


def build_repair_hints(
    vocab_violations: list[VocabViolation],
    shacl_violations: list[ShaclViolation],
) -> list[str]:
    hints: list[str] = []

    for v in vocab_violations:
        if v.term_kind == "property":
            hints.append(
                f"Remove or replace undeclared predicate `{v.term}` with a property declared in the domain ontology."
            )
        else:
            hints.append(
                f"Replace undeclared class `{v.term}` with a declared class from the domain ontology."
            )

    for s in shacl_violations:
        hints.append(f"Fix SHACL violation: {s.message}")

    if vocab_violations and shacl_violations:
        hints.insert(
            0,
            "Run vocabulary gate first: SHACL cannot see fabricated terms in open-world mode.",
        )

    return hints
