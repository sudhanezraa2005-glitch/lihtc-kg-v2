"""Loader for State nodes."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from neo4j import Driver

from .base_loader import BaseLoader, run_loader_from_cli


class StateLoader(BaseLoader):
    """Loader for State nodes from geography datasets."""

    REQUIRED_COLUMNS: ClassVar[list[str]] = ["state_fips", "state_abbr", "state_name"]

    def __init__(self, driver: Driver, batch_size: int = 1000) -> None:
        """Initialize State loader.

        Args:
            driver: Neo4j driver instance.
            batch_size: Number of records per batch (default: 1000).
        """
        super().__init__(driver, "State", "state_fips", batch_size)

    def load_from_parquet(self, parquet_path: str, dry_run: bool = False) -> int:
        """Load State nodes from parquet file.

        Args:
            parquet_path: Path to states.parquet file.
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
        self.logger.info(f"Loaded {len(df)} State records from {parquet_path}")
        self.validate_schema(df, self.REQUIRED_COLUMNS, parquet_path)

        if dry_run:
            self.logger.info(f"Dry-run: verified schema for {len(df)} State records")
            return len(df)

        merge_cypher = """
        UNWIND $batch AS row
        MERGE (s:State {state_fips: row.state_fips})
        ON CREATE SET
            s.state_abbr = row.state_abbr,
            s.state_name = row.state_name
        ON MATCH SET
            s.state_abbr = COALESCE(row.state_abbr, s.state_abbr),
            s.state_name = COALESCE(row.state_name, s.state_name)
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
        self.logger.info(f"State load complete. Total nodes: {final_count}")
        return final_count


def main() -> None:
    """Run State loader from the command line."""
    run_loader_from_cli(
        StateLoader,
        "data/gold/geography/states.parquet",
        "Load State nodes into Neo4j",
        1000,
    )


if __name__ == "__main__":
    main()
