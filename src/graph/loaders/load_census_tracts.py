"""Loader for CensusTract nodes."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from neo4j import Driver

from .base_loader import BaseLoader, run_loader_from_cli


class CensusTractLoader(BaseLoader):
    """Loader for CensusTract nodes from tract reference dataset."""

    REQUIRED_COLUMNS: ClassVar[list[str]] = [
        "tract_fips",
        "county_fips",
        "state_fips",
        "county_code",
        "tract_code",
        "tract_name",
    ]

    def __init__(self, driver: Driver, batch_size: int = 5000) -> None:
        """Initialize CensusTract loader.

        Args:
            driver: Neo4j driver instance.
            batch_size: Number of records per batch (default: 5000).
        """
        super().__init__(driver, "CensusTract", "tract_fips", batch_size)

    def load_from_parquet(self, parquet_path: str, dry_run: bool = False) -> int:
        """Load CensusTract nodes from parquet file.

        Args:
            parquet_path: Path to tract_reference.parquet file.
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
        self.logger.info(f"Loaded {len(df)} CensusTract records from {parquet_path}")
        self.validate_schema(df, self.REQUIRED_COLUMNS, parquet_path)

        tract_df = df.loc[:, self.REQUIRED_COLUMNS].drop_duplicates(
            subset="tract_fips",
            keep="first",
        )
        self.logger.info(f"Deduplicated to {len(tract_df)} unique tracts")

        if dry_run:
            self.logger.info(f"Dry-run: verified schema for {len(tract_df)} unique CensusTract records")
            return len(tract_df)

        merge_cypher = """
        UNWIND $batch AS row
        MERGE (t:CensusTract {tract_fips: row.tract_fips})
        ON CREATE SET
            t.county_fips = row.county_fips,
            t.state_fips = row.state_fips,
            t.county_code = row.county_code,
            t.tract_code = row.tract_code,
            t.tract_name = row.tract_name
        ON MATCH SET
            t.county_fips = COALESCE(row.county_fips, t.county_fips),
            t.state_fips = COALESCE(row.state_fips, t.state_fips),
            t.county_code = COALESCE(row.county_code, t.county_code),
            t.tract_code = COALESCE(row.tract_code, t.tract_code),
            t.tract_name = COALESCE(row.tract_name, t.tract_name)
        """

        for batch_index in range(0, len(tract_df), self.batch_size):
            batch_df = tract_df.iloc[batch_index : batch_index + self.batch_size]
            records = self._prepare_batch(batch_df)
            self.logger.debug(
                f"Processing batch {batch_index // self.batch_size + 1} ({len(records)} records)"
            )
            self.execute_batch(merge_cypher, records)
            self.logger.info(f"Completed batch {batch_index // self.batch_size + 1}")

        final_count = self.get_node_count()
        self.logger.info(f"CensusTract load complete. Total nodes: {final_count}")
        return final_count


def main() -> None:
    """Run CensusTract loader from the command line."""
    run_loader_from_cli(
        CensusTractLoader,
        "data/silver/geography/tract_reference.parquet",
        "Load CensusTract nodes into Neo4j",
        5000,
    )


if __name__ == "__main__":
    main()
