"""Orchestrate Neo4j relationship loading for the FHFA knowledge graph."""

from __future__ import annotations

import argparse
import logging
import sys

from src.graph.config.neo4j_config import Neo4jConfig
from src.graph.relationships import (
    BaseRelationshipLoader,
    ConformingLimitCountyRelationshipLoader,
    CountyFMRRelationshipLoader,
    CountyMetroAreaRelationshipLoader,
    CountyStateRelationshipLoader,
    HPITractRelationshipLoader,
    RelationshipLoadStats,
    TractCountyRelationshipLoader,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_all_relationships(
    neo4j_uri: str | None = None,
    neo4j_user: str | None = None,
    neo4j_password: str | None = None,
    batch_size: int = 10000,
    dry_run: bool = False,
) -> list[RelationshipLoadStats]:
    """Load all graph relationships in dependency order.

    Args:
        neo4j_uri: Neo4j connection URI, or NEO4J_URI from environment.
        neo4j_user: Neo4j username, or NEO4J_USER from environment.
        neo4j_password: Neo4j password, or NEO4J_PASSWORD from environment.
        batch_size: Number of source nodes to inspect per batch.
        dry_run: If True, validate and estimate coverage without writing.

    Returns:
        Per-relationship loading statistics.
    """
    if not Neo4jConfig.validate_env_vars() and not all([neo4j_uri, neo4j_user, neo4j_password]):
        raise ValueError(
            "Must provide Neo4j credentials via environment variables "
            "(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) or function arguments"
        )

    config = Neo4jConfig(neo4j_uri, neo4j_user, neo4j_password)
    driver = config.get_driver()
    logger.info("Connected to Neo4j at %s", config.uri)

    try:
        loaders: list[tuple[str, BaseRelationshipLoader]] = [
            ("State -> County", CountyStateRelationshipLoader(driver, batch_size)),
            ("County -> CensusTract", TractCountyRelationshipLoader(driver, batch_size)),
            ("CensusTract -> HPISnapshot", HPITractRelationshipLoader(driver, batch_size)),
            (
                "County -> ConformingLimitSnapshot",
                ConformingLimitCountyRelationshipLoader(driver, batch_size),
            ),
            ("County -> FMRSnapshot", CountyFMRRelationshipLoader(driver, batch_size)),
            ("County -> MetroArea", CountyMetroAreaRelationshipLoader(driver, batch_size)),
        ]

        results: list[RelationshipLoadStats] = []
        for relationship_name, loader in loaders:
            logger.info("Loading relationship: %s", relationship_name)
            stats = loader.load(dry_run=dry_run)
            results.append(stats)
            logger.info(
                "%s complete: eligible=%s matched=%s created=%s dry_run=%s",
                relationship_name,
                stats.eligible_source_count,
                stats.matched_target_count,
                stats.relationships_created,
                stats.dry_run,
            )

        total_created = sum(result.relationships_created for result in results)
        total_matched = sum(result.matched_target_count for result in results)
        logger.info(
            "Relationship loading complete: total_matched=%s total_created=%s dry_run=%s",
            total_matched,
            total_created,
            dry_run,
        )
        return results
    finally:
        driver.close()
        logger.info("Neo4j connection closed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load all Neo4j relationships")
    parser.add_argument("--uri", help="Neo4j URI (default: env NEO4J_URI)")
    parser.add_argument("--user", help="Neo4j username (default: env NEO4J_USER)")
    parser.add_argument("--password", help="Neo4j password (default: env NEO4J_PASSWORD)")
    parser.add_argument("--batch-size", type=int, default=10000, help="Source nodes per batch")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing relationships")
    args = parser.parse_args()

    try:
        load_all_relationships(
            neo4j_uri=args.uri,
            neo4j_user=args.user,
            neo4j_password=args.password,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
        sys.exit(0)
    except Exception as exc:
        logger.error("Relationship loading failed: %s", exc)
        sys.exit(1)
