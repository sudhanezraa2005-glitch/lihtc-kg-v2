"""Loader for MetroArea nodes."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from neo4j import Driver

from .base_loader import BaseLoader, run_loader_from_cli


class MetroAreaLoader(BaseLoader):
    """Loader for MetroArea nodes from geography datasets."""

    REQUIRED_COLUMNS: ClassVar[list[str]] = ["cbsa_code"]

    def __init__(self, driver: Driver, batch_size: int = 1000) -> None:
        """Initialize MetroArea loader.

        Args:
            driver: Neo4j driver instance.
            batch_size: Number of records per batch (default: 1000).
        """
        super().__init__(driver, "MetroArea", "cbsa_code", batch_size)

    def load_from_parquet(self, parquet_path: str, dry_run: bool = False) -> int:
        """Load MetroArea nodes from parquet file.

        Args:
            parquet_path: Path to metro_areas.parquet file.
            dry_run: If True, validate schema and estimate node count without writing.

        Returns:
            Number of records processed or nodes estimated.

        Raises:
            FileNotFoundError: If parquet file does not exist.
            ValueError: If required columns are missing.
            Exception: If any Cypher execution fails.
        """
        path = Path(parquet_path)
        if not path.exists():
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

        df = pd.read_parquet(path)
        self.logger.info(f"Loaded {len(df)} MetroArea records from {parquet_path}")
        self.validate_schema(df, self.REQUIRED_COLUMNS, parquet_path)

        if dry_run:
            self.logger.info(f"Dry-run: verified schema for {len(df)} MetroArea records")
            return len(df)

        merge_cypher = """
        UNWIND $batch AS row
        MERGE (m:MetroArea {cbsa_code: row.cbsa_code})
        ON CREATE SET
            m.cbsa_code = row.cbsa_code
        """

        for batch_index in range(0, len(df), self.batch_size):
            batch_df = df.iloc[batch_index : batch_index + self.batch_size]
            records = self._prepare_batch(batch_df)
            self.logger.debug(
                f"Processing batch {batch_index // self.batch_size + 1} ({len(records)} records)"
            )
            self.execute_batch(merge_cypher, records)
            self.logger.info(f"Completed batch {batch_index // self.batch_size + 1}")

        final_count = self.get_node_count()
        self.logger.info(f"MetroArea load complete. Total nodes: {final_count}")
        return final_count


def main() -> None:
    """Run MetroArea loader from the command line."""
    run_loader_from_cli(
        MetroAreaLoader,
        "data/gold/geography/metro_areas.parquet",
        "Load MetroArea nodes into Neo4j",
        1000,
    )


if __name__ == "__main__":
    main()
