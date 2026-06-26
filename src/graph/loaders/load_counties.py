"""Loader for County nodes."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from neo4j import Driver

from .base_loader import BaseLoader, run_loader_from_cli


class CountyLoader(BaseLoader):
    """Loader for County nodes from geography datasets."""

    REQUIRED_COLUMNS: ClassVar[list[str]] = [
        "county_fips",
        "state_fips",
        "county_code",
        "county_name",
        "cbsa_number",
    ]

    def __init__(self, driver: Driver, batch_size: int = 5000) -> None:
        """Initialize County loader.

        Args:
            driver: Neo4j driver instance.
            batch_size: Number of records per batch (default: 5000).
        """
        super().__init__(driver, "County", "county_fips", batch_size)

    def load_from_parquet(self, parquet_path: str, dry_run: bool = False) -> int:
        """Load County nodes from parquet file.

        The County node is sourced from conforming_limits.parquet, which provides
        richer metadata (county_name, cbsa_number) compared to tract_reference.

        Args:
            parquet_path: Path to conforming_limits.parquet file.
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
        self.logger.info(f"Loaded {len(df)} County records from {parquet_path}")
        self.validate_schema(df, self.REQUIRED_COLUMNS, parquet_path)

        county_df = df.loc[:, self.REQUIRED_COLUMNS].drop_duplicates(
            subset="county_fips",
            keep="first",
        )
        self.logger.info(f"Deduplicated to {len(county_df)} unique counties")

        if dry_run:
            self.logger.info(f"Dry-run: verified schema for {len(county_df)} unique County records")
            return len(county_df)

        merge_cypher = """
        UNWIND $batch AS row
        MERGE (c:County {county_fips: row.county_fips})
        ON CREATE SET
            c.state_fips = row.state_fips,
            c.county_code = row.county_code,
            c.county_name = row.county_name,
            c.cbsa_number = row.cbsa_number
        ON MATCH SET
            c.state_fips = COALESCE(row.state_fips, c.state_fips),
            c.county_code = COALESCE(row.county_code, c.county_code),
            c.county_name = COALESCE(row.county_name, c.county_name),
            c.cbsa_number = COALESCE(row.cbsa_number, c.cbsa_number)
        """

        for batch_index in range(0, len(county_df), self.batch_size):
            batch_df = county_df.iloc[batch_index : batch_index + self.batch_size]
            records = self._prepare_batch(batch_df)
            self.logger.debug(
                f"Processing batch {batch_index // self.batch_size + 1} ({len(records)} records)"
            )
            self.execute_batch(merge_cypher, records)
            self.logger.info(f"Completed batch {batch_index // self.batch_size + 1}")

        final_count = self.get_node_count()
        self.logger.info(f"County load complete. Total nodes: {final_count}")
        return final_count


def main() -> None:
    """Run County loader from the command line."""
    run_loader_from_cli(
        CountyLoader,
        "data/silver/fhfa/conforming_limits.parquet",
        "Load County nodes into Neo4j",
        5000,
    )


if __name__ == "__main__":
    main()
