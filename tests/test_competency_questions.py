from rdflib import Graph, Namespace
from rdflib.namespace import RDF

from validator.competency_questions import check_competency_questions
from validator.engine import ValidationEngine

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
    assert result.competency_violations == []


def test_score_out_of_range_fails_competency_ask(biomedical_domain):
    turtle = """
    @prefix bio: <https://ontoharness.dev/biomedical#> .
    bio:gene1 a bio:Gene ;
        bio:hasSymbol "BRCA1" ;
        bio:associatedWith bio:disease1 ;
        bio:hasScore "1.5"^^<http://www.w3.org/2001/XMLSchema#decimal> .
    bio:disease1 a bio:Disease ;
        bio:hasIdentifier "MONDO:0007254" .
    """
    engine = ValidationEngine(biomedical_domain)
    result = engine.validate_turtle(turtle)
    assert result.conforms is False
    assert any(v.cq_id == "cq-association-score" for v in result.competency_violations)


def test_gene_missing_association_fails_competency_select(biomedical_domain):
    turtle = """
    @prefix bio: <https://ontoharness.dev/biomedical#> .
    bio:gene1 a bio:Gene ;
        bio:hasSymbol "BRCA1" ;
        bio:hasScore "0.5"^^<http://www.w3.org/2001/XMLSchema#decimal> .
    bio:disease1 a bio:Disease ;
        bio:hasIdentifier "MONDO:0007254" .
    """
    engine = ValidationEngine(biomedical_domain)
    result = engine.validate_turtle(turtle)
    assert result.conforms is False
    assert any(v.cq_id == "cq-gene-symbol" for v in result.competency_violations)


def test_optional_competency_questions_not_enforced(biomedical_domain):
    data = Graph()
    data.parse(data=VALID_TURTLE, format="turtle")
    violations = check_competency_questions(data, biomedical_domain.competency_questions)
    assert all(v.cq_id != "cq-hypothesis-label" for v in violations)
