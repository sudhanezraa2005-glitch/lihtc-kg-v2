"""Loader for County HAS_FMR FMRSnapshot relationships."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import LiteralString

from neo4j import Driver

from src.graph.config.neo4j_config import Neo4jConfig

from .base_relationship_loader import BaseRelationshipLoader


class CountyFMRRelationshipLoader(BaseRelationshipLoader):
    """Load (:County)-[:HAS_FMR]->(:FMRSnapshot) relationships."""

    source_label: LiteralString = "County"
    target_label: LiteralString = "FMRSnapshot"
    relationship_type: LiteralString = "HAS_FMR"
    source_match_key: LiteralString = "county_fips"
    source_join_key: LiteralString = "county_fips"
    target_match_key: LiteralString = "county_fips"
    target_business_key: LiteralString = "snapshot_id"

    def __init__(self, driver: Driver, batch_size: int = 10000) -> None:
        super().__init__(driver, batch_size)


def main() -> int:
    """Run County HAS_FMR relationship loader from the command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    parser = argparse.ArgumentParser(description="Load County HAS_FMR FMRSnapshot relationships")
    parser.add_argument("--uri", help="Neo4j URI (default: env NEO4J_URI)")
    parser.add_argument("--user", help="Neo4j username (default: env NEO4J_USER)")
    parser.add_argument("--password", help="Neo4j password (default: env NEO4J_PASSWORD)")
    parser.add_argument("--batch-size", type=int, default=10000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = Neo4jConfig(args.uri, args.user, args.password)
    driver = config.get_driver()
    try:
        loader = CountyFMRRelationshipLoader(driver, args.batch_size)
        loader.load(dry_run=args.dry_run)
        return 0
    except Exception as exc:
        logging.getLogger(__name__).error("County HAS_FMR relationship load failed: %s", exc)
        return 1
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
