"""Apply Neo4j indexes for the FHFA graph."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import LiteralString, cast

from neo4j import Driver

from src.graph.config.neo4j_config import Neo4jConfig
from src.graph.setup.validate_schema import INDEXES_PATH, read_cypher_statements, validate_indexes


logger = logging.getLogger(__name__)


def apply_indexes(driver: Driver) -> int:
    """Execute all index statements and verify required indexes exist."""
    statements = read_cypher_statements(INDEXES_PATH)
    with driver.session() as session:
        for statement in statements:
            logger.info("Applying index: %s", statement)
            session.run(cast(LiteralString, statement)).consume()

    missing_indexes = validate_indexes(driver)
    if missing_indexes:
        missing = ", ".join(
            f"{spec.label}({', '.join(spec.property_names)})" for spec in missing_indexes
        )
        raise RuntimeError(f"Missing indexes after apply: {missing}")

    logger.info("Applied and verified %s indexes", len(statements))
    return len(statements)


def apply_indexes_from_config(
    neo4j_uri: str | None = None,
    neo4j_user: str | None = None,
    neo4j_password: str | None = None,
) -> int:
    """Create a Neo4j driver from config and apply indexes."""
    config = Neo4jConfig(neo4j_uri, neo4j_user, neo4j_password)
    driver = config.get_driver()
    try:
        return apply_indexes(driver)
    finally:
        driver.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    parser = argparse.ArgumentParser(description="Apply FHFA Neo4j indexes")
    parser.add_argument("--uri", help="Neo4j URI (default: env NEO4J_URI)")
    parser.add_argument("--user", help="Neo4j username (default: env NEO4J_USER)")
    parser.add_argument("--password", help="Neo4j password (default: env NEO4J_PASSWORD)")
    args = parser.parse_args()

    try:
        apply_indexes_from_config(args.uri, args.user, args.password)
        return 0
    except Exception as exc:
        logger.error("Failed to apply indexes: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
