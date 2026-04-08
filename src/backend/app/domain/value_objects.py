"""Value objects — immutable, equality by value, self-validating.

Value objects represent concepts that are defined by their attributes,
not by identity. Two Email("x@y.com") are the same regardless of
when or where they were created.

Use instead of raw strings/ints when the value has constraints or behavior.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Email:
    """Validated email address."""
    value: str

    def __post_init__(self):
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", self.value):
            raise ValueError(f"Invalid email: {self.value}")

    def __str__(self) -> str:
        return self.value

    @property
    def domain(self) -> str:
        return self.value.split("@")[1]


@dataclass(frozen=True)
class Percentage:
    """A value between 0 and 100."""
    value: float

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError(f"Percentage must be 0-100, got {self.value}")

    def __str__(self) -> str:
        return f"{self.value:.1f}%"


@dataclass(frozen=True)
class Money:
    """Monetary amount with currency."""
    amount: float
    currency: str = "USD"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError(f"Money cannot be negative: {self.amount}")
        if len(self.currency) != 3:
            raise ValueError(f"Currency must be 3-letter ISO code: {self.currency}")

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)


@dataclass(frozen=True)
class GeoPoint:
    """Geographic coordinate."""
    lat: float
    lng: float

    def __post_init__(self):
        if not -90 <= self.lat <= 90:
            raise ValueError(f"Latitude must be -90 to 90, got {self.lat}")
        if not -180 <= self.lng <= 180:
            raise ValueError(f"Longitude must be -180 to 180, got {self.lng}")

    def __str__(self) -> str:
        return f"({self.lat:.6f}, {self.lng:.6f})"


@dataclass(frozen=True)
class DateRange:
    """A range between two dates. Start must be before end."""
    start: str  # ISO format YYYY-MM-DD
    end: str

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError(f"Start {self.start} must be before end {self.end}")

    @property
    def days(self) -> int:
        from datetime import date
        d1 = date.fromisoformat(self.start)
        d2 = date.fromisoformat(self.end)
        return (d2 - d1).days
