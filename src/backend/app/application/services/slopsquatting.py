"""Slopsquatting detection service.

Receives a package name and checks it against all known popular packages
across all seeded ecosystems using two complementary strategies:

1. Damerau-Levenshtein distance — catches simple typos (reqeusts → requests)
2. Fuzzy Jaccard — tokenizes by delimiters, then fuzzy-matches tokens using DL
   distance. Catches structural confusions (python_dateutl → python-dateutil)

Both strategies run in parallel; results are merged and de-duplicated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import structlog

from app.domain.slopsquatting.entities import PopularPackage
from app.domain.slopsquatting.interfaces import AbstractPopularPackageRepository
from app.domain.slopsquatting.value_objects import SlopsquatResult, TypoMatch

logger = structlog.get_logger(__name__)

# Delimiters used to split package names into word tokens
_DELIMITER_RE = re.compile(r"[-_.\s]+")


# ---------------------------------------------------------------------------
# Damerau-Levenshtein distance (full optimal, not restricted edit distance)
# ---------------------------------------------------------------------------


def damerau_levenshtein(a: str, b: str) -> int:
    """Compute the Damerau-Levenshtein distance between two strings.

    Includes insertions, deletions, substitutions, and *adjacent transpositions*.
    Uses the optimal string alignment variant (no substring edits after transposition).
    """
    len_a, len_b = len(a), len(b)
    # Fast paths
    if len_a == 0:
        return len_b
    if len_b == 0:
        return len_a
    if a == b:
        return 0

    # Matrix of size (len_a+1) x (len_b+1)
    d = [[0] * (len_b + 1) for _ in range(len_a + 1)]
    for i in range(len_a + 1):
        d[i][0] = i
    for j in range(len_b + 1):
        d[0][j] = j

    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,       # deletion
                d[i][j - 1] + 1,       # insertion
                d[i - 1][j - 1] + cost,  # substitution
            )
            # transposition
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + cost)

    return d[len_a][len_b]


# ---------------------------------------------------------------------------
# Tokenization helpers
# ---------------------------------------------------------------------------


def tokenize(name: str) -> list[str]:
    """Split a package name by delimiters into lowercase word tokens.

    Example: "Flask-SQLAlchemy" → ["flask", "sqlalchemy"]
    """
    return [t for t in _DELIMITER_RE.split(name.lower()) if t]


# ---------------------------------------------------------------------------
# Fuzzy Jaccard similarity
# ---------------------------------------------------------------------------


def _best_token_distance(token: str, candidates: list[str]) -> int:
    """Return the minimum DL distance of *token* to any candidate token."""
    if not candidates:
        return len(token)  # worst case
    return min(damerau_levenshtein(token, c) for c in candidates)


def fuzzy_jaccard(name_a: str, name_b: str, token_dl_threshold: int = 1) -> float:
    """Compute fuzzy Jaccard similarity.

    Tokenizes both names, then for each token in A finds the best matching
    token in B via DL distance.  A token-pair counts as a match if
    DL distance ≤ token_dl_threshold.

    Returns a value in [0.0, 1.0].  1.0 = perfect fuzzy match.
    """
    tokens_a = tokenize(name_a)
    tokens_b = tokenize(name_b)

    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0

    # Count fuzzy matches (A→B and B→A), then use Jaccard formula
    matches_ab = sum(
        1 for t in tokens_a if _best_token_distance(t, tokens_b) <= token_dl_threshold
    )
    matches_ba = sum(
        1 for t in tokens_b if _best_token_distance(t, tokens_a) <= token_dl_threshold
    )

    # Symmetric fuzzy intersection = average of both directions
    fuzzy_intersection = (matches_ab + matches_ba) / 2.0
    union_size = len(tokens_a) + len(tokens_b) - fuzzy_intersection

    if union_size <= 0:
        return 1.0

    return fuzzy_intersection / union_size


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------


def _dl_confidence(distance: int, max_len: int) -> float:
    """Convert a DL distance into a confidence score [0, 1].

    Lower distance + longer name = higher confidence of typosquat.
    """
    if max_len == 0:
        return 0.0
    # Normalized distance (0 = identical, 1 = fully different)
    normalized = distance / max(max_len, 1)
    # Invert: close match → high confidence
    return round(max(0.0, 1.0 - normalized), 4)


def _fj_confidence(similarity: float) -> float:
    """Convert fuzzy Jaccard similarity directly to confidence."""
    return round(similarity, 4)


# ---------------------------------------------------------------------------
# Detection service
# ---------------------------------------------------------------------------


@dataclass
class SlopsquattingService:
    """Orchestrates typosquat / slopsquat detection."""

    repository: AbstractPopularPackageRepository

    # Configurable thresholds (can be overridden per-request)
    dl_threshold: int = 2
    fj_similarity_threshold: float = 0.6

    async def analyze(
        self,
        name: str,
        *,
        top_n: int = 10,
        dl_threshold: int | None = None,
        fj_threshold: float | None = None,
    ) -> SlopsquatResult:
        """Analyze a package name against all seeded ecosystems.

        Args:
            name: the package name to check
            top_n: max number of matches to return
            dl_threshold: override Damerau-Levenshtein max distance
            fj_threshold: override fuzzy Jaccard min similarity

        Returns:
            SlopsquatResult with matches from all ecosystems.
        """
        dl_max = dl_threshold if dl_threshold is not None else self.dl_threshold
        fj_min = fj_threshold if fj_threshold is not None else self.fj_similarity_threshold

        query_lower = name.lower().strip()

        # Load all popular packages from DB
        all_packages = await self.repository.get_all_names()

        logger.info(
            "slopsquatting_analyze",
            query=query_lower,
            candidates=len(all_packages),
        )

        # Check for exact match
        exact_matches = [p for p in all_packages if p.name.lower() == query_lower]
        exact_match_found = len(exact_matches) > 0

        # If exact match, not suspicious
        if exact_match_found:
            return SlopsquatResult(
                query_name=name,
                is_suspicious=False,
                exact_match_found=True,
                matches=(),
            )

        # Run both detection strategies
        matches: list[TypoMatch] = []
        seen: set[tuple[str, str]] = set()  # (matched_package, ecosystem)

        for pkg in all_packages:
            pkg_lower = pkg.name.lower()

            # Skip exact match (already handled)
            if pkg_lower == query_lower:
                continue

            # Strategy 1: Damerau-Levenshtein on full string
            dl_dist = damerau_levenshtein(query_lower, pkg_lower)
            if 0 < dl_dist <= dl_max:
                key = (pkg.name, pkg.ecosystem)
                if key not in seen:
                    seen.add(key)
                    matches.append(
                        TypoMatch(
                            package_name=name,
                            matched_package=pkg.name,
                            ecosystem=pkg.ecosystem,
                            distance=dl_dist,
                            method="damerau-levenshtein",
                            confidence=_dl_confidence(dl_dist, max(len(query_lower), len(pkg_lower))),
                        )
                    )

            # Strategy 2: Fuzzy Jaccard
            fj_sim = fuzzy_jaccard(query_lower, pkg_lower)
            if fj_sim >= fj_min:
                key = (pkg.name, pkg.ecosystem)
                if key not in seen:
                    seen.add(key)
                    matches.append(
                        TypoMatch(
                            package_name=name,
                            matched_package=pkg.name,
                            ecosystem=pkg.ecosystem,
                            distance=dl_dist,
                            method="fuzzy-jaccard",
                            confidence=_fj_confidence(fj_sim),
                        )
                    )

        # Sort by confidence desc, take top N
        matches.sort(key=lambda m: m.confidence, reverse=True)
        top_matches = tuple(matches[:top_n])

        return SlopsquatResult(
            query_name=name,
            is_suspicious=len(top_matches) > 0,
            exact_match_found=False,
            matches=top_matches,
        )
