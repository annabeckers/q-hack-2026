"""Specification pattern — composable query predicates in domain language.

Specifications encapsulate query logic as first-class objects that can
be combined with AND/OR/NOT. They translate to SQLAlchemy filters
in the infrastructure layer.

Usage:
    # Define specs
    active = IsActive()
    admin = HasEmail("admin@example.com")

    # Combine
    active_admin = active & admin
    non_admin = active & ~admin

    # Use in repository
    users = await repo.find(active_admin)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class Specification(ABC):
    """Base specification — composable with &, |, ~."""

    @abstractmethod
    def is_satisfied_by(self, entity: Any) -> bool:
        """Check in-memory (useful for testing)."""
        ...

    def __and__(self, other: "Specification") -> "AndSpecification":
        return AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "OrSpecification":
        return OrSpecification(self, other)

    def __invert__(self) -> "NotSpecification":
        return NotSpecification(self)


@dataclass
class AndSpecification(Specification):
    left: Specification
    right: Specification

    def is_satisfied_by(self, entity: Any) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)


@dataclass
class OrSpecification(Specification):
    left: Specification
    right: Specification

    def is_satisfied_by(self, entity: Any) -> bool:
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)


@dataclass
class NotSpecification(Specification):
    spec: Specification

    def is_satisfied_by(self, entity: Any) -> bool:
        return not self.spec.is_satisfied_by(entity)


# ── Concrete Specifications ─────────────────────────────────


@dataclass
class IsActive(Specification):
    def is_satisfied_by(self, entity: Any) -> bool:
        return getattr(entity, "is_active", False)


@dataclass
class HasEmail(Specification):
    email: str

    def is_satisfied_by(self, entity: Any) -> bool:
        return getattr(entity, "email", "") == self.email


@dataclass
class HasSourceType(Specification):
    source_type: str

    def is_satisfied_by(self, entity: Any) -> bool:
        return getattr(entity, "source_type", "") == self.source_type


@dataclass
class CreatedAfter(Specification):
    after: str  # ISO datetime string

    def is_satisfied_by(self, entity: Any) -> bool:
        created = getattr(entity, "created_at", None)
        if not created:
            return False
        from datetime import datetime
        return created > datetime.fromisoformat(self.after)
