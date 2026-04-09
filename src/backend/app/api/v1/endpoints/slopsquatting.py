"""Slopsquatting detection API endpoints.

POST /analyze  — check a package name against all seeded ecosystems
POST /seed     — one-shot fetch of top packages from ecosyste.ms into DB
GET  /stats    — show counts of seeded packages per ecosystem
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.application.services.slopsquatting import SlopsquattingService
from app.infrastructure.ecosystems_client import EcosystemsClient
from app.infrastructure.repositories.popular_package_repository import PopularPackageRepository

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=500, description="Package name to check")
    top_n: int = Field(10, ge=1, le=50, description="Max matches to return")
    dl_threshold: int | None = Field(None, ge=1, le=5, description="Override Damerau-Levenshtein max distance")
    fj_threshold: float | None = Field(None, ge=0.0, le=1.0, description="Override fuzzy Jaccard min similarity")


class TypoMatchResponse(BaseModel):
    package_name: str
    matched_package: str
    ecosystem: str
    distance: int
    method: str
    confidence: float


class AnalyzeResponse(BaseModel):
    query_name: str
    is_suspicious: bool
    exact_match_found: bool
    matches: list[TypoMatchResponse]


class SeedRequest(BaseModel):
    ecosystems: list[str] = Field(
        default=["pypi", "npm", "crates"],
        description="Ecosystem labels to seed (pypi, npm, crates)",
    )
    per_page: int = Field(100, ge=10, le=100, description="Results per page from ecosyste.ms")
    pages: int = Field(5, ge=1, le=20, description="Number of pages to fetch per ecosystem")


class SeedResponse(BaseModel):
    seeded: dict[str, int]
    total: int


class StatsResponse(BaseModel):
    ecosystems: dict[str, int]
    total: int


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_repository(request: Request) -> PopularPackageRepository:
    container = request.app.state.container
    return PopularPackageRepository(container.db_session_factory)


def _get_service(request: Request) -> SlopsquattingService:
    repo = _get_repository(request)
    return SlopsquattingService(repository=repo)


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_package(body: AnalyzeRequest, request: Request):
    """Check a package name for potential typosquatting / slopsquatting.

    Runs Damerau-Levenshtein and fuzzy Jaccard against all known popular
    packages across all seeded ecosystems. No ecosystem parameter needed —
    this is intentionally ecosystem-agnostic to reduce burden on LLM callers.
    """
    service = _get_service(request)
    result = await service.analyze(
        name=body.name,
        top_n=body.top_n,
        dl_threshold=body.dl_threshold,
        fj_threshold=body.fj_threshold,
    )

    return AnalyzeResponse(
        query_name=result.query_name,
        is_suspicious=result.is_suspicious,
        exact_match_found=result.exact_match_found,
        matches=[TypoMatchResponse(**asdict(m)) for m in result.matches],
    )


@router.post("/seed", response_model=SeedResponse)
async def seed_packages(body: SeedRequest, request: Request):
    """One-shot: fetch top popular packages from ecosyste.ms and store in DB.

    This is a hackathon convenience endpoint — run once to populate the
    popular_packages table. Subsequent calls upsert (safe to re-run).
    """
    from app.infrastructure.ecosystems_client import DEFAULT_REGISTRIES

    repo = _get_repository(request)

    # Filter to requested ecosystems
    registries = {k: v for k, v in DEFAULT_REGISTRIES.items() if k in body.ecosystems}
    if not registries:
        return SeedResponse(seeded={}, total=0)

    client = EcosystemsClient()
    all_packages = await client.seed_all(
        registries=registries,
        per_page=body.per_page,
        pages=body.pages,
    )

    seeded: dict[str, int] = {}
    total = 0
    for eco, pkgs in all_packages.items():
        count = await repo.save_batch(pkgs)
        seeded[eco] = count
        total += count

    return SeedResponse(seeded=seeded, total=total)


@router.get("/stats", response_model=StatsResponse)
async def package_stats(request: Request):
    """Show counts of seeded popular packages per ecosystem."""
    repo = _get_repository(request)
    counts = await repo.count_by_ecosystem()
    return StatsResponse(ecosystems=counts, total=sum(counts.values()))
