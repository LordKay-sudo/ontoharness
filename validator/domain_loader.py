from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from rdflib import Graph


@dataclass(frozen=True)
class DomainBundle:
    name: str
    label: str
    description: str
    ontology_graph: Graph
    shapes_graph: Graph
    policed_namespaces: tuple[str, ...]
    competency_questions: tuple[dict[str, Any], ...]


def load_domain(domain_dir: Path) -> DomainBundle:
    manifest_path = domain_dir / "domain.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing domain manifest: {manifest_path}")

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    ontology_path = domain_dir / manifest["ontology"]
    shapes_path = domain_dir / manifest["shapes"]
    cq_path = domain_dir / manifest.get("competency_questions", "competency_questions.yaml")

    ontology_graph = Graph()
    ontology_graph.parse(ontology_path, format="turtle")

    shapes_graph = Graph()
    if shapes_path.is_file():
        shapes_graph.parse(shapes_path, format="turtle")

    cqs: tuple[dict[str, Any], ...] = ()
    if cq_path.is_file():
        cq_doc = yaml.safe_load(cq_path.read_text(encoding="utf-8")) or {}
        cqs = tuple(cq_doc.get("competency_questions", []))

    policed = tuple(manifest.get("policed_namespaces", []))

    return DomainBundle(
        name=manifest.get("domain", domain_dir.name),
        label=manifest.get("label", domain_dir.name),
        description=manifest.get("description", ""),
        ontology_graph=ontology_graph,
        shapes_graph=shapes_graph,
        policed_namespaces=policed,
        competency_questions=cqs,
    )


def load_domains(domains_root: Path) -> dict[str, DomainBundle]:
    bundles: dict[str, DomainBundle] = {}
    if not domains_root.is_dir():
        return bundles
    for entry in sorted(domains_root.iterdir()):
        if entry.is_dir() and (entry / "domain.yaml").is_file():
            bundle = load_domain(entry)
            bundles[bundle.name] = bundle
    return bundles
