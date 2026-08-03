from __future__ import annotations

from dataclasses import dataclass

from pyshacl import validate as shacl_validate
from rdflib import Graph


@dataclass(frozen=True)
class ShaclViolation:
    message: str
    path: str | None = None
    focus_node: str | None = None
    source_shape: str | None = None


def check_shacl(data: Graph, ontology: Graph, shapes: Graph) -> tuple[bool, list[ShaclViolation]]:
    if len(shapes) == 0:
        return True, []

    combined_ontology = Graph()
    for triple in ontology:
        combined_ontology.add(triple)
    for triple in shapes:
        combined_ontology.add(triple)

    conforms, results_graph, results_text = shacl_validate(
        data_graph=data,
        shacl_graph=shapes,
        ont_graph=combined_ontology,
        inference="none",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
        meta_shacl=False,
        advanced=True,
        js=False,
        debug=False,
    )

    violations: list[ShaclViolation] = []
    if not conforms:
        # Prefer structured parse; fall back to line-based text
        if results_text:
            for line in results_text.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("Validation Report"):
                    violations.append(ShaclViolation(message=stripped))
        if not violations:
            violations.append(ShaclViolation(message="SHACL validation failed (see shapes)."))

    return bool(conforms), violations
