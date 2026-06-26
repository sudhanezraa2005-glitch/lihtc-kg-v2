"""Orchestrate FHFA Neo4j schema setup, loading, and validation."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

from load_all_relationships import load_all_relationships
from src.graph.config.neo4j_config import Neo4jConfig
from src.graph.loaders.load_census_tracts import CensusTractLoader
from src.graph.loaders.load_conforming_limit_snapshots import ConformingLimitSnapshotLoader
from src.graph.loaders.load_counties import CountyLoader
from src.graph.loaders.load_fmr_snapshots import FMRSnapshotLoader
from src.graph.loaders.load_hpi_snapshots import HPISnapshotLoader
from src.graph.loaders.load_metro_areas import MetroAreaLoader
from src.graph.loaders.load_states import StateLoader
from src.graph.setup.apply_constraints import apply_constraints
from src.graph.setup.apply_indexes import apply_indexes
from src.graph.setup.validate_schema import validate_schema
from src.graph.validation.validate_graph import validate_graph


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_all_nodes(
    neo4j_uri: str | None = None,
    neo4j_user: str | None = None,
    neo4j_password: str | None = None,
    data_dir: str = "data",
) -> None:
    """Apply schema, load graph data, load relationships, and validate the graph.

    Execution order:
    1. Apply constraints
    2. Apply indexes
    3. Validate schema
    4. Load nodes
    5. Load relationships
    6. Run graph validation
    """
    logger.info("Starting FHFA Neo4j graph load...")

    if not Neo4jConfig.validate_env_vars() and not all([neo4j_uri, neo4j_user, neo4j_password]):
        raise ValueError(
            "Must provide Neo4j credentials via environment variables "
            "(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) or function arguments"
        )

    config = Neo4jConfig(neo4j_uri, neo4j_user, neo4j_password)
    driver = config.get_driver()
    logger.info("Connected to Neo4j at %s", config.uri)

    try:
        logger.info("Applying Neo4j constraints...")
        apply_constraints(driver)

        logger.info("Applying Neo4j indexes...")
        apply_indexes(driver)

        logger.info("Validating Neo4j schema...")
        validate_schema(driver)

        loaders = [
            ("State", StateLoader(driver, batch_size=1000), f"{data_dir}/gold/geography/states.parquet"),
            ("MetroArea", MetroAreaLoader(driver, batch_size=1000), f"{data_dir}/gold/geography/metro_areas.parquet"),
            ("County", CountyLoader(driver, batch_size=5000), f"{data_dir}/silver/fhfa/conforming_limits.parquet"),
            ("FMRSnapshot", FMRSnapshotLoader(driver, batch_size=5000), f"{data_dir}/gold/hud/fmr_snapshots.parquet"),
            ("CensusTract", CensusTractLoader(driver, batch_size=5000), f"{data_dir}/silver/geography/tract_reference.parquet"),
            ("ConformingLimitSnapshot", ConformingLimitSnapshotLoader(driver, batch_size=5000), f"{data_dir}/silver/fhfa/conforming_limits.parquet"),
            ("HPISnapshot", HPISnapshotLoader(driver, batch_size=10000), f"{data_dir}/gold/fhfa/tract_hpi_enriched.parquet"),
        ]

        results: dict[str, int] = {}
        for node_label, loader, data_path in loaders:
            logger.info("Loading %s nodes from %s", node_label, data_path)
            if not Path(data_path).exists():
                raise FileNotFoundError(f"Data file not found: {data_path}")

            node_count = loader.load_from_parquet(data_path)
            results[node_label] = node_count
            logger.info("OK %s load successful (%s nodes)", node_label, node_count)

        total_nodes = sum(results.values())
        logger.info("Neo4j node loading summary")
        for node_label, count in results.items():
            logger.info("%s: %s nodes", node_label, f"{count:,}")
        logger.info("TOTAL: %s nodes", f"{total_nodes:,}")

        logger.info("Loading graph relationships...")
        load_all_relationships(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
        )

        logger.info("Running graph validation...")
        validation_report = validate_graph(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
        )
        if not validation_report.ready_for_full_load:
            raise RuntimeError("Graph validation failed: READY_FOR_FULL_LOAD = FALSE")
        logger.info("OK Graph validation passed")

    except Exception as exc:
        logger.error("FAILED Graph loading failed: %s", exc)
        raise
    finally:
        driver.close()
        logger.info("Neo4j connection closed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load and validate the FHFA Neo4j graph")
    parser.add_argument("--uri", help="Neo4j URI (default: env NEO4J_URI)")
    parser.add_argument("--user", help="Neo4j username (default: env NEO4J_USER)")
    parser.add_argument("--password", help="Neo4j password (default: env NEO4J_PASSWORD)")
    parser.add_argument("--data-dir", default="data", help="Root data directory (default: data)")
    args = parser.parse_args()

    try:
        load_all_nodes(
            neo4j_uri=args.uri,
            neo4j_user=args.user,
            neo4j_password=args.password,
            data_dir=args.data_dir,
        )
        sys.exit(0)
    except Exception as exc:
        logger.error("Fatal error: %s", exc)
        sys.exit(1)
