from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, XSD

from validator.engine import ValidationEngine
from validator.vocab_gate import check_vocabulary

BIO = Namespace("https://ontoharness.dev/biomedical#")


VALID_TURTLE = """
@prefix bio: <https://ontoharness.dev/biomedical#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

bio:gene1 a bio:Gene ;
    bio:hasSymbol "BRCA1" ;
    bio:associatedWith bio:disease1 ;
    bio:hasScore "0.92"^^<http://www.w3.org/2001/XMLSchema#decimal> .

bio:disease1 a bio:Disease ;
    bio:hasIdentifier "MONDO:0007254" .
"""

FABRICATED_PREDICATE_TURTLE = """
@prefix bio: <https://ontoharness.dev/biomedical#> .

bio:gene1 a bio:Gene ;
    bio:hasTherapeuticTarget bio:disease1 .

bio:disease1 a bio:Disease .
"""


def test_valid_biomedical_graph_conforms(biomedical_domain):
    engine = ValidationEngine(biomedical_domain)
    result = engine.validate_turtle(VALID_TURTLE)
    assert result.conforms is True
    assert result.vocab_violations == []
    assert result.shacl_violations == []


def test_fabricated_predicate_fails_vocab_gate(biomedical_domain):
    engine = ValidationEngine(biomedical_domain)
    result = engine.validate_turtle(FABRICATED_PREDICATE_TURTLE)
    assert result.conforms is False
    assert any("hasTherapeuticTarget" in v.term for v in result.vocab_violations)
    assert result.repair_hints


def test_vocab_gate_catches_undeclared_class(biomedical_domain):
    data = Graph()
    data.add((BIO.gene1, RDF.type, BIO.FabricatedDisease))
    violations = check_vocabulary(
        data,
        biomedical_domain.ontology_graph,
        biomedical_domain.policed_namespaces,
    )
    assert any("FabricatedDisease" in v.term for v in violations)


def test_missing_score_fails_shacl(biomedical_domain):
    turtle = """
    @prefix bio: <https://ontoharness.dev/biomedical#> .
    bio:gene1 a bio:Gene ;
        bio:hasSymbol "BRCA1" ;
        bio:associatedWith bio:disease1 .
    bio:disease1 a bio:Disease ;
        bio:hasIdentifier "MONDO:0007254" .
    """
    engine = ValidationEngine(biomedical_domain)
    result = engine.validate_turtle(turtle)
    assert result.conforms is False
    assert result.shacl_violations
