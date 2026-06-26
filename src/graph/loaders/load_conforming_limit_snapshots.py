"""Loader for ConformingLimitSnapshot nodes."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from neo4j import Driver

from .base_loader import BaseLoader, run_loader_from_cli


class ConformingLimitSnapshotLoader(BaseLoader):
    """Loader for ConformingLimitSnapshot nodes from conforming limits dataset."""

    REQUIRED_COLUMNS: ClassVar[list[str]] = [
        "snapshot_id",
        "county_fips",
        "state_fips",
        "county_code",
        "county_name",
        "state_abbr",
        "cbsa_number",
        "limit_1_unit",
        "limit_2_unit",
        "limit_3_unit",
        "limit_4_unit",
        "year",
        "source_type",
    ]

    def __init__(self, driver: Driver, batch_size: int = 5000) -> None:
        """Initialize ConformingLimitSnapshot loader.

        Args:
            driver: Neo4j driver instance.
            batch_size: Number of records per batch (default: 5000).
        """
        super().__init__(driver, "ConformingLimitSnapshot", "snapshot_id", batch_size)

    def load_from_parquet(self, parquet_path: str, dry_run: bool = False) -> int:
        """Load ConformingLimitSnapshot nodes from parquet file.

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
        self.logger.info(f"Loaded {len(df)} ConformingLimitSnapshot records from {parquet_path}")
        self.validate_schema(df, self.REQUIRED_COLUMNS, parquet_path)

        if dry_run:
            self.logger.info(f"Dry-run: verified schema for {len(df)} ConformingLimitSnapshot records")
            return len(df)

        merge_cypher = """
        UNWIND $batch AS row
        MERGE (l:ConformingLimitSnapshot {snapshot_id: row.snapshot_id})
        ON CREATE SET
            l.county_fips = row.county_fips,
            l.state_fips = row.state_fips,
            l.county_code = row.county_code,
            l.county_name = row.county_name,
            l.state_abbr = row.state_abbr,
            l.cbsa_number = row.cbsa_number,
            l.limit_1_unit = row.limit_1_unit,
            l.limit_2_unit = row.limit_2_unit,
            l.limit_3_unit = row.limit_3_unit,
            l.limit_4_unit = row.limit_4_unit,
            l.year = row.year,
            l.source_type = row.source_type
        ON MATCH SET
            l.county_fips = COALESCE(row.county_fips, l.county_fips),
            l.state_fips = COALESCE(row.state_fips, l.state_fips),
            l.county_code = COALESCE(row.county_code, l.county_code),
            l.county_name = COALESCE(row.county_name, l.county_name),
            l.state_abbr = COALESCE(row.state_abbr, l.state_abbr),
            l.cbsa_number = COALESCE(row.cbsa_number, l.cbsa_number),
            l.limit_1_unit = COALESCE(row.limit_1_unit, l.limit_1_unit),
            l.limit_2_unit = COALESCE(row.limit_2_unit, l.limit_2_unit),
            l.limit_3_unit = COALESCE(row.limit_3_unit, l.limit_3_unit),
            l.limit_4_unit = COALESCE(row.limit_4_unit, l.limit_4_unit),
            l.year = COALESCE(row.year, l.year),
            l.source_type = COALESCE(row.source_type, l.source_type)
        """

        total_records = len(df)
        for batch_index in range(0, total_records, self.batch_size):
            batch_df = df.iloc[batch_index : batch_index + self.batch_size]
            records = self._prepare_batch(batch_df)
            self.logger.debug(
                f"Processing batch {batch_index // self.batch_size + 1} ({len(records)} records, {batch_index}/{total_records})"
            )
            self.execute_batch(merge_cypher, records)
            self.logger.info(f"Completed batch {batch_index // self.batch_size + 1}")

        final_count = self.get_node_count()
        self.logger.info(f"ConformingLimitSnapshot load complete. Total nodes: {final_count}")
        return final_count


def main() -> None:
    """Run ConformingLimitSnapshot loader from the command line."""
    run_loader_from_cli(
        ConformingLimitSnapshotLoader,
        "data/silver/fhfa/conforming_limits.parquet",
        "Load ConformingLimitSnapshot nodes into Neo4j",
        5000,
    )


if __name__ == "__main__":
    main()
