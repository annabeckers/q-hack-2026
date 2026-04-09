"""Unit tests for slopsquatting detection algorithms.

Tests the pure functions (Damerau-Levenshtein, fuzzy Jaccard, tokenizer)
without any database or network dependencies.
"""

import pytest

from app.application.services.slopsquatting import (
    SlopsquattingService,
    damerau_levenshtein,
    fuzzy_jaccard,
    tokenize,
)
from app.domain.slopsquatting.entities import PopularPackage
from app.domain.slopsquatting.interfaces import AbstractPopularPackageRepository


# ---------------------------------------------------------------------------
# Damerau-Levenshtein distance tests
# ---------------------------------------------------------------------------


class TestDamerauLevenshtein:
    def test_identical_strings(self):
        assert damerau_levenshtein("requests", "requests") == 0

    def test_single_insertion(self):
        assert damerau_levenshtein("reqests", "requests") == 1

    def test_single_deletion(self):
        assert damerau_levenshtein("requestss", "requests") == 1

    def test_single_substitution(self):
        assert damerau_levenshtein("reqnests", "requests") == 1

    def test_adjacent_transposition(self):
        # DL distance for transposition should be 1, not 2 (unlike plain Levenshtein)
        assert damerau_levenshtein("reqeusts", "requests") == 1

    def test_empty_strings(self):
        assert damerau_levenshtein("", "") == 0
        assert damerau_levenshtein("abc", "") == 3
        assert damerau_levenshtein("", "abc") == 3

    def test_completely_different(self):
        assert damerau_levenshtein("abc", "xyz") == 3

    def test_common_typosquats(self):
        assert damerau_levenshtein("numppy", "numpy") <= 2
        assert damerau_levenshtein("pandsa", "pandas") <= 2
        assert damerau_levenshtein("flaask", "flask") <= 2


# ---------------------------------------------------------------------------
# Tokenizer tests
# ---------------------------------------------------------------------------


class TestTokenize:
    def test_hyphen_split(self):
        assert tokenize("flask-sqlalchemy") == ["flask", "sqlalchemy"]

    def test_underscore_split(self):
        assert tokenize("python_dateutil") == ["python", "dateutil"]

    def test_dot_split(self):
        assert tokenize("oslo.config") == ["oslo", "config"]

    def test_mixed_delimiters(self):
        assert tokenize("my-cool_pkg.v2") == ["my", "cool", "pkg", "v2"]

    def test_single_word(self):
        assert tokenize("requests") == ["requests"]

    def test_case_normalization(self):
        assert tokenize("Flask-SQLAlchemy") == ["flask", "sqlalchemy"]


# ---------------------------------------------------------------------------
# Fuzzy Jaccard tests
# ---------------------------------------------------------------------------


class TestFuzzyJaccard:
    def test_identical_names(self):
        assert fuzzy_jaccard("flask-sqlalchemy", "flask-sqlalchemy") == 1.0

    def test_different_delimiters(self):
        # Same tokens, different delimiters → should be 1.0
        sim = fuzzy_jaccard("flask-sqlalchemy", "flask_sqlalchemy")
        assert sim == 1.0

    def test_one_token_typo(self):
        # "sqlaclhemy" is DL=1 from "sqlalchemy" → fuzzy match
        sim = fuzzy_jaccard("flask-sqlaclhemy", "flask-sqlalchemy")
        assert sim >= 0.6

    def test_completely_different(self):
        sim = fuzzy_jaccard("xyz-abc", "flask-sqlalchemy")
        assert sim < 0.3

    def test_subset_tokens(self):
        # "flask" is a subset of "flask-sqlalchemy" tokens
        sim = fuzzy_jaccard("flask", "flask-sqlalchemy")
        assert 0.0 < sim < 1.0

    def test_empty_strings(self):
        assert fuzzy_jaccard("", "") == 1.0


# ---------------------------------------------------------------------------
# Integration-style test with in-memory repository
# ---------------------------------------------------------------------------


class InMemoryPopularPackageRepository(AbstractPopularPackageRepository):
    """Simple in-memory repository for testing."""

    def __init__(self, packages: list[PopularPackage]):
        self._packages = packages

    async def get_all_names(self) -> list[PopularPackage]:
        return self._packages

    async def get_by_ecosystem(self, ecosystem: str) -> list[PopularPackage]:
        return [p for p in self._packages if p.ecosystem == ecosystem]

    async def find_by_name(self, name: str) -> list[PopularPackage]:
        return [p for p in self._packages if p.name.lower() == name.lower()]

    async def save_batch(self, packages: list[PopularPackage]) -> int:
        self._packages.extend(packages)
        return len(packages)

    async def count_by_ecosystem(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for p in self._packages:
            counts[p.ecosystem] = counts.get(p.ecosystem, 0) + 1
        return counts


@pytest.fixture
def sample_packages() -> list[PopularPackage]:
    return [
        PopularPackage(name="requests", ecosystem="pypi", downloads=1000000),
        PopularPackage(name="numpy", ecosystem="pypi", downloads=900000),
        PopularPackage(name="pandas", ecosystem="pypi", downloads=800000),
        PopularPackage(name="flask", ecosystem="pypi", downloads=700000),
        PopularPackage(name="flask-sqlalchemy", ecosystem="pypi", downloads=500000),
        PopularPackage(name="python-dateutil", ecosystem="pypi", downloads=600000),
        PopularPackage(name="express", ecosystem="npm", downloads=2000000),
        PopularPackage(name="lodash", ecosystem="npm", downloads=1500000),
        PopularPackage(name="react", ecosystem="npm", downloads=3000000),
    ]


@pytest.fixture
def service(sample_packages: list[PopularPackage]) -> SlopsquattingService:
    repo = InMemoryPopularPackageRepository(sample_packages)
    return SlopsquattingService(repository=repo)


class TestSlopsquattingService:
    @pytest.mark.asyncio
    async def test_exact_match_not_suspicious(self, service: SlopsquattingService):
        result = await service.analyze("requests")
        assert not result.is_suspicious
        assert result.exact_match_found

    @pytest.mark.asyncio
    async def test_typosquat_detected_dl(self, service: SlopsquattingService):
        result = await service.analyze("reqeusts")
        assert result.is_suspicious
        assert any(m.matched_package == "requests" for m in result.matches)

    @pytest.mark.asyncio
    async def test_typosquat_detected_numppy(self, service: SlopsquattingService):
        result = await service.analyze("numppy")
        assert result.is_suspicious
        assert any(m.matched_package == "numpy" for m in result.matches)

    @pytest.mark.asyncio
    async def test_completely_unknown_not_suspicious(self, service: SlopsquattingService):
        result = await service.analyze("zzzzzzzzzzz")
        assert not result.is_suspicious

    @pytest.mark.asyncio
    async def test_cross_ecosystem_detection(self, service: SlopsquattingService):
        # "recat" should match "react" from npm ecosystem
        result = await service.analyze("recat")
        assert result.is_suspicious
        assert any(m.ecosystem == "npm" and m.matched_package == "react" for m in result.matches)

    @pytest.mark.asyncio
    async def test_fuzzy_jaccard_catches_delimiter_confusion(self, service: SlopsquattingService):
        # "flask_sqlaclhemy" vs "flask-sqlalchemy" — different delimiter + typo in token
        result = await service.analyze("flask_sqlaclhemy")
        assert result.is_suspicious
        assert any(m.matched_package == "flask-sqlalchemy" for m in result.matches)

    @pytest.mark.asyncio
    async def test_fuzzy_jaccard_catches_delimiter_confusion_correct_name(self, service: SlopsquattingService):
        # "flask_sqlalchemy" vs "flask-sqlalchemy" — different delimiter + no typo in token
        result = await service.analyze("flask_sqlalchemy")
        assert result.is_suspicious
        assert any(m.matched_package == "flask-sqlalchemy" for m in result.matches)

    @pytest.mark.asyncio
    async def test_top_n_limits_results(self, service: SlopsquattingService):
        result = await service.analyze("a", top_n=2)
        assert len(result.matches) <= 2
