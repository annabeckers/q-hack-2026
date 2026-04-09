"""Configuration loader for deterministic analysis rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_CONFIG_PATH = Path(__file__).resolve().parents[4] / "config" / "deterministic_rules.yaml"


@dataclass(frozen=True)
class CategoryRules:
    by_table: dict[str, str] = field(default_factory=dict)
    by_field: dict[str, str] = field(default_factory=dict)

    def resolve(self, table: str, field: str) -> str:
        """Resolve category for a given table/field combination."""
        # Field-level override takes priority
        if field in self.by_field:
            return self.by_field[field]
        # Fall back to table default
        return self.by_table.get(table, "secret")


@dataclass(frozen=True)
class SeverityRules:
    by_field: dict[str, str] = field(default_factory=dict)
    by_table_field: dict[str, dict[str, str]] = field(default_factory=dict)
    default: str = "medium"

    def resolve(self, table: str, field: str, base_severity: str = "") -> str:
        """Resolve severity with priority: by_field > by_table_field > base > default."""
        # Priority 1: Field name override
        if field in self.by_field:
            return self.by_field[field]

        # Priority 2: Table + field combination
        table_config = self.by_table_field.get(table, {})
        if field in table_config:
            return table_config[field]

        # Priority 3: Preserve critical/high from base if set
        if base_severity in {"critical", "high"}:
            return base_severity

        # Priority 4: Default
        return self.default


@dataclass(frozen=True)
class DeterministicRulesConfig:
    category_rules: CategoryRules = field(default_factory=CategoryRules)
    severity_rules: SeverityRules = field(default_factory=SeverityRules)
    department_keywords: dict[str, list[str]] = field(default_factory=dict)

    def infer_department(self, text: str | None) -> str | None:
        """Infer department from keywords in text."""
        haystack = (text or "").lower()
        for department, keywords in self.department_keywords.items():
            if any(keyword in haystack for keyword in keywords):
                return department
        return None


def load_deterministic_rules_config(path: Path | None = None) -> DeterministicRulesConfig:
    """Load deterministic rules configuration from YAML file."""
    config_file = path or _CONFIG_PATH

    if not config_file.exists():
        # Return default configuration if file not found
        return DeterministicRulesConfig()

    with open(config_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return DeterministicRulesConfig(
        category_rules=CategoryRules(
            by_table=data.get("category_rules", {}).get("by_table", {}),
            by_field=data.get("category_rules", {}).get("by_field", {}),
        ),
        severity_rules=SeverityRules(
            by_field=data.get("severity_rules", {}).get("by_field", {}),
            by_table_field=data.get("severity_rules", {}).get("by_table_field", {}),
            default=data.get("severity_rules", {}).get("default", "medium"),
        ),
        department_keywords=data.get("department_keywords", {}),
    )


# Singleton instance for default configuration
_default_config: DeterministicRulesConfig | None = None


def get_deterministic_rules_config() -> DeterministicRulesConfig:
    """Get the default deterministic rules configuration (cached)."""
    global _default_config
    if _default_config is None:
        _default_config = load_deterministic_rules_config()
    return _default_config


def reset_config_cache() -> None:
    """Reset the cached configuration (useful for testing)."""
    global _default_config
    _default_config = None
