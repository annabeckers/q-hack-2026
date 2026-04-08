"""Domain events — decouple side effects from business logic.

Events are emitted by entities/handlers and consumed by event handlers.
This keeps the domain layer pure: the entity says "this happened",
infrastructure decides what to do about it.

Usage:
    # In a handler:
    user = User(email="x@y.com", ...)
    events.emit(UserCreated(user_id=user.id, email=user.email))

    # In infrastructure:
    @events.on(UserCreated)
    async def send_welcome_email(event: UserCreated):
        ...
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine
from uuid import UUID, uuid4

# ── Event Base ──────────────────────────────────────────────


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events. Immutable."""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ── Concrete Events ────────────────────────────────────────


@dataclass(frozen=True)
class UserCreated(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    email: str = ""


@dataclass(frozen=True)
class UserLoggedIn(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    email: str = ""


@dataclass(frozen=True)
class DocumentIngested(DomainEvent):
    document_id: UUID = field(default_factory=uuid4)
    source: str = ""
    source_type: str = ""


@dataclass(frozen=True)
class DataSourceSynced(DomainEvent):
    data_source_id: UUID = field(default_factory=uuid4)
    name: str = ""
    records_count: int = 0


@dataclass(frozen=True)
class AgentDecisionMade(DomainEvent):
    agent: str = ""
    decision: str = ""
    trigger: str = ""


# ── Event Bus (in-process, sync-first) ─────────────────────

_handlers: dict[type, list[Callable]] = {}


def on(event_type: type[DomainEvent]):
    """Decorator to register an event handler."""
    def decorator(fn: Callable):
        _handlers.setdefault(event_type, []).append(fn)
        return fn
    return decorator


async def emit(event: DomainEvent) -> None:
    """Emit an event to all registered handlers."""
    handlers = _handlers.get(type(event), [])
    for handler in handlers:
        result = handler(event)
        if isinstance(result, Coroutine):
            await result


def clear_handlers() -> None:
    """Clear all handlers. Useful for testing."""
    _handlers.clear()
