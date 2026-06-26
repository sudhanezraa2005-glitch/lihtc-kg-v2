"""Apply Neo4j constraints for the FHFA graph."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import LiteralString, cast

from neo4j import Driver

from src.graph.config.neo4j_config import Neo4jConfig
from src.graph.setup.validate_schema import CONSTRAINTS_PATH, read_cypher_statements, validate_constraints


logger = logging.getLogger(__name__)


def apply_constraints(driver: Driver) -> int:
    """Execute all constraint statements and verify required constraints exist."""
    statements = read_cypher_statements(CONSTRAINTS_PATH)
    with driver.session() as session:
        for statement in statements:
            logger.info("Applying constraint: %s", statement)
            session.run(cast(LiteralString, statement)).consume()

    missing_constraints = validate_constraints(driver)
    if missing_constraints:
        missing = ", ".join(
            f"{spec.label}({spec.property_name})" for spec in missing_constraints
        )
        raise RuntimeError(f"Missing constraints after apply: {missing}")

    logger.info("Applied and verified %s constraints", len(statements))
    return len(statements)


def apply_constraints_from_config(
    neo4j_uri: str | None = None,
    neo4j_user: str | None = None,
    neo4j_password: str | None = None,
) -> int:
    """Create a Neo4j driver from config and apply constraints."""
    config = Neo4jConfig(neo4j_uri, neo4j_user, neo4j_password)
    driver = config.get_driver()
    try:
        return apply_constraints(driver)
    finally:
        driver.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    parser = argparse.ArgumentParser(description="Apply FHFA Neo4j constraints")
    parser.add_argument("--uri", help="Neo4j URI (default: env NEO4J_URI)")
    parser.add_argument("--user", help="Neo4j username (default: env NEO4J_USER)")
    parser.add_argument("--password", help="Neo4j password (default: env NEO4J_PASSWORD)")
    args = parser.parse_args()

    try:
        apply_constraints_from_config(args.uri, args.user, args.password)
        return 0
    except Exception as exc:
        logger.error("Failed to apply constraints: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
