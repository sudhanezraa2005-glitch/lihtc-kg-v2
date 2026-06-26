"""Validate Neo4j constraints and indexes for the FHFA graph."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import logging
from pathlib import Path
import re
import sys
from typing import Any, LiteralString, cast

from neo4j import Driver

from src.graph.config.neo4j_config import Neo4jConfig


logger = logging.getLogger(__name__)

GRAPH_DIR = Path(__file__).resolve().parents[1]
CONSTRAINTS_PATH = GRAPH_DIR / "constraints.cypher"
INDEXES_PATH = GRAPH_DIR / "indexes.cypher"


@dataclass(frozen=True)
class ConstraintSpec:
    """Required Neo4j uniqueness constraint."""

    label: str
    property_name: str


@dataclass(frozen=True)
class IndexSpec:
    """Required Neo4j index."""

    label: str
    property_names: tuple[str, ...]


@dataclass(frozen=True)
class SchemaValidationResult:
    """Schema validation summary."""

    missing_constraints: list[ConstraintSpec]
    missing_indexes: list[IndexSpec]

    @property
    def is_valid(self) -> bool:
        return not self.missing_constraints and not self.missing_indexes


def read_cypher_statements(path: Path) -> list[str]:
    """Read semicolon-delimited Cypher statements, ignoring line comments."""
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        lines.append(line)

    cypher = "\n".join(lines)
    return [statement.strip() for statement in cypher.split(";") if statement.strip()]


def required_constraints(path: Path = CONSTRAINTS_PATH) -> list[ConstraintSpec]:
    """Parse required uniqueness constraints from constraints.cypher."""
    specs: list[ConstraintSpec] = []
    pattern = re.compile(
        r"FOR\s*\(\w+:(?P<label>\w+)\)\s*REQUIRE\s+\w+\.(?P<property>\w+)\s+IS\s+UNIQUE",
        re.IGNORECASE,
    )
    for statement in read_cypher_statements(path):
        match = pattern.search(statement)
        if match:
            specs.append(
                ConstraintSpec(
                    label=match.group("label"),
                    property_name=match.group("property"),
                )
            )
    return specs


def required_indexes(path: Path = INDEXES_PATH) -> list[IndexSpec]:
    """Parse required indexes from indexes.cypher."""
    specs: list[IndexSpec] = []
    pattern = re.compile(
        r"FOR\s*\(\w+:(?P<label>\w+)\)\s*ON\s*\((?P<properties>[^)]+)\)",
        re.IGNORECASE,
    )
    for statement in read_cypher_statements(path):
        match = pattern.search(statement)
        if not match:
            continue
        properties = tuple(
            property_ref.strip().split(".")[-1].strip("`")
            for property_ref in match.group("properties").split(",")
        )
        specs.append(IndexSpec(label=match.group("label"), property_names=properties))
    return specs


def validate_constraints(driver: Driver) -> list[ConstraintSpec]:
    """Return required constraints that are missing from Neo4j."""
    existing_constraints = _existing_constraints(driver)
    return [
        spec
        for spec in required_constraints()
        if (spec.label, spec.property_name) not in existing_constraints
    ]


def validate_indexes(driver: Driver) -> list[IndexSpec]:
    """Return required indexes that are missing from Neo4j."""
    existing_indexes = _existing_indexes(driver)
    return [
        spec
        for spec in required_indexes()
        if (spec.label, spec.property_names) not in existing_indexes
    ]


def validate_schema(driver: Driver) -> SchemaValidationResult:
    """Validate all required Neo4j constraints and indexes."""
    result = SchemaValidationResult(
        missing_constraints=validate_constraints(driver),
        missing_indexes=validate_indexes(driver),
    )
    if not result.is_valid:
        messages = []
        if result.missing_constraints:
            messages.append(
                "Missing constraints: "
                + ", ".join(
                    f"{spec.label}({spec.property_name})" for spec in result.missing_constraints
                )
            )
        if result.missing_indexes:
            messages.append(
                "Missing indexes: "
                + ", ".join(
                    f"{spec.label}({', '.join(spec.property_names)})"
                    for spec in result.missing_indexes
                )
            )
        raise RuntimeError("; ".join(messages))

    logger.info("Neo4j schema validation passed")
    return result


def _existing_constraints(driver: Driver) -> set[tuple[str, str]]:
    with driver.session() as session:
        result = session.run(cast(LiteralString, "SHOW CONSTRAINTS"))
        constraints: set[tuple[str, str]] = set()
        for record in result:
            values = dict(record)
            labels = _as_string_list(values.get("labelsOrTypes"))
            properties = _as_string_list(values.get("properties"))
            for label in labels:
                for property_name in properties:
                    constraints.add((label, property_name))
        return constraints


def _existing_indexes(driver: Driver) -> set[tuple[str, tuple[str, ...]]]:
    with driver.session() as session:
        result = session.run(cast(LiteralString, "SHOW INDEXES"))
        indexes: set[tuple[str, tuple[str, ...]]] = set()
        for record in result:
            values = dict(record)
            labels = _as_string_list(values.get("labelsOrTypes"))
            properties = tuple(_as_string_list(values.get("properties")))
            if not properties:
                continue
            for label in labels:
                indexes.add((label, properties))
        return indexes


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def validate_schema_from_config(
    neo4j_uri: str | None = None,
    neo4j_user: str | None = None,
    neo4j_password: str | None = None,
) -> SchemaValidationResult:
    """Create a Neo4j driver from config and validate schema."""
    config = Neo4jConfig(neo4j_uri, neo4j_user, neo4j_password)
    driver = config.get_driver()
    try:
        return validate_schema(driver)
    finally:
        driver.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    parser = argparse.ArgumentParser(description="Validate FHFA Neo4j schema")
    parser.add_argument("--uri", help="Neo4j URI (default: env NEO4J_URI)")
    parser.add_argument("--user", help="Neo4j username (default: env NEO4J_USER)")
    parser.add_argument("--password", help="Neo4j password (default: env NEO4J_PASSWORD)")
    args = parser.parse_args()

    try:
        validate_schema_from_config(args.uri, args.user, args.password)
        return 0
    except Exception as exc:
        logger.error("Neo4j schema validation failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
