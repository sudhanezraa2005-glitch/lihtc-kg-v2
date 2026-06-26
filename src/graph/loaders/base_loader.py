"""Base loader for Neo4j node ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
import argparse
import logging
from collections.abc import Callable, Sequence
from typing import Any, LiteralString, cast

import numpy as np
import pandas as pd
from neo4j import Driver

from src.graph.config.neo4j_config import Neo4jConfig


def normalize_value(value: Any) -> Any | None:
    """Convert pandas and numpy scalar values into Neo4j-safe Python values."""
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.to_pydatetime()
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        if np.isnan(value):
            return None
        return float(value)

    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass

    return value


class BaseLoader(ABC):
    """Base class for Neo4j node loaders."""

    def __init__(
        self,
        driver: Driver,
        node_label: str,
        business_key: str,
        batch_size: int = 5000,
    ) -> None:
        """Initialize the base loader.

        Args:
            driver: Neo4j driver instance.
            node_label: Label for the node type (e.g., 'State').
            business_key: Property name for the unique business key.
            batch_size: Number of records to process per batch.
        """
        self.driver = driver
        self.node_label = node_label
        self.business_key = business_key
        self.batch_size = batch_size
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_schema(
        self,
        df: pd.DataFrame,
        required_columns: Sequence[str],
        source_path: str,
    ) -> None:
        """Validate that required columns exist in the source dataframe.

        Args:
            df: Loaded DataFrame.
            required_columns: List of columns required for the loader.
            source_path: Path to the source file for error context.

        Raises:
            ValueError: If required columns are missing.
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns in {source_path}: {missing_columns}. "
                f"Expected columns: {required_columns}"
            )

    def _prepare_properties(self, row: pd.Series) -> dict[str, Any]:
        """Convert a pandas Series row to Neo4j properties.

        Args:
            row: A pandas Series representing a row.

        Returns:
            Dictionary of properties suitable for Neo4j.
        """
        props: dict[str, Any] = {}
        for key, value in row.items():
            normalized_value = normalize_value(value)
            if normalized_value is None:
                continue
            props[str(key)] = normalized_value
        return props

    def _prepare_batch(self, batch_df: pd.DataFrame) -> list[dict[str, Any]]:
        """Prepare a batch of rows for Neo4j parameter binding.

        Args:
            batch_df: DataFrame containing rows for the batch.

        Returns:
            List of dictionaries for batch execution.
        """
        batch_records: list[dict[str, Any]] = []
        for _, row in batch_df.iterrows():
            record = self._prepare_properties(row)
            if record:
                batch_records.append(record)
        return batch_records

    def execute_batch(
        self,
        merge_cypher: LiteralString,
        batch: Sequence[dict[str, Any]],
    ) -> None:
        """Execute a single batch using one Neo4j session and one transaction.

        Args:
            merge_cypher: Cypher statement with UNWIND support.
            batch: List of row dictionaries to execute.

        Raises:
            Exception: If the batch execution fails.
        """
        if not batch:
            return

        try:
            with self.driver.session() as session:
                tx = session.begin_transaction()
                tx.run(merge_cypher, batch=batch)
                tx.commit()
        except Exception as e:
            self.logger.error(
                f"Failed to execute batch for {self.node_label} ({len(batch)} rows): {e}"
            )
            raise

    @abstractmethod
    def load_from_parquet(self, parquet_path: str, dry_run: bool = False) -> int:
        """Load nodes from a parquet file.

        Args:
            parquet_path: Path to the parquet file.
            dry_run: If True, validate without writing nodes.

        Returns:
            Estimated number of nodes processed.

        Raises:
            NotImplementedError: Subclasses must implement this method.
        """
        raise NotImplementedError

    def get_node_count(self) -> int:
        """Get the current count of nodes with this label.

        Returns:
            Number of nodes with the label.
        """
        with self.driver.session() as session:
            count_cypher = cast(
                LiteralString,
                f"MATCH (n:{self.node_label}) RETURN COUNT(n) AS count",
            )
            result = session.run(count_cypher)
            record = result.single()
            if record is None:
                return 0
            count = record["count"]
            if not isinstance(count, int):
                raise TypeError(
                    f"Expected Neo4j count for {self.node_label} to be int, got {type(count).__name__}"
                )
            return count


def run_loader_from_cli(
    loader_factory: Callable[[Driver, int], BaseLoader],
    default_parquet_path: str,
    description: str,
    default_batch_size: int,
) -> None:
    """Run a node loader from a module CLI entrypoint."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--parquet-path",
        default=default_parquet_path,
        help=f"Source parquet path (default: {default_parquet_path})",
    )
    parser.add_argument("--uri", help="Neo4j URI (default: env NEO4J_URI)")
    parser.add_argument("--user", help="Neo4j username (default: env NEO4J_USER)")
    parser.add_argument("--password", help="Neo4j password (default: env NEO4J_PASSWORD)")
    parser.add_argument("--batch-size", type=int, default=default_batch_size)
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing nodes")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = Neo4jConfig(args.uri, args.user, args.password)
    driver = config.get_driver()
    try:
        loader = loader_factory(driver, args.batch_size)
        node_count = loader.load_from_parquet(args.parquet_path, dry_run=args.dry_run)
        loader.logger.info("Loader complete. Records/nodes reported: %s", node_count)
    finally:
        driver.close()
