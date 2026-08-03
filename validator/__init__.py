"""OntoHarness validation engine — closed-world vocab gate + SHACL."""

from validator.engine import ValidationEngine, ValidationResult
from validator.domain_loader import DomainBundle, load_domain

__all__ = ["ValidationEngine", "ValidationResult", "DomainBundle", "load_domain"]
