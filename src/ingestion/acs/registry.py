"""Registry helpers for ACS ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REGISTRY_PATH = Path("metadata/acs/table_registry.yaml")


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    """Load ACS table registry YAML."""
    if not path.exists():
        raise FileNotFoundError(f"ACS registry not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"ACS registry must be a mapping: {path}")
    return data


def enabled_years(registry: dict[str, Any]) -> list[int]:
    return [int(year) for year in registry["acs"]["years"]]


def years_for_table(registry: dict[str, Any], table: str) -> list[int]:
    table_years = registry["tables"][table].get("years")
    if table_years:
        return [int(year) for year in table_years]
    return enabled_years(registry)


def enabled_states(registry: dict[str, Any]) -> list[str]:
    return [str(state).zfill(2) for state in registry["acs"]["states"]]


def enabled_tables(registry: dict[str, Any]) -> list[str]:
    return [str(table) for table in registry["acs"]["enabled_tables"]]
