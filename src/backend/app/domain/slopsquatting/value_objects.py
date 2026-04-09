"""Value objects for slopsquatting detection results — immutable, equality by value."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TypoMatch:
    """A single match between a queried package name and a known package."""

    package_name: str  # the queried (suspicious) name
    matched_package: str  # the known-good package it resembles
    ecosystem: str
    distance: int  # Damerau-Levenshtein edit distance (full-string)
    method: str  # "damerau-levenshtein" | "fuzzy-jaccard"
    confidence: float  # 0.0 – 1.0, higher = more suspicious

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0–1, got {self.confidence}")


@dataclass(frozen=True)
class SlopsquatResult:
    """Aggregated analysis result for a package name check."""

    query_name: str
    is_suspicious: bool
    exact_match_found: bool  # True if the package name exists as-is in DB
    matches: tuple[TypoMatch, ...] = field(default_factory=tuple)
