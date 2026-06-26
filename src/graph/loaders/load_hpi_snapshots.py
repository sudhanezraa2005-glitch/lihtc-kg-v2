"""Loader for HPISnapshot nodes."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from neo4j import Driver

from .base_loader import BaseLoader, run_loader_from_cli


class HPISnapshotLoader(BaseLoader):
    """Loader for HPISnapshot nodes from HPI time-series dataset."""

    REQUIRED_COLUMNS: ClassVar[list[str]] = [
        "snapshot_id",
        "tract_fips",
        "county_fips",
        "state_fips",
        "year",
        "hpi",
        "annual_change",
        "hpi1990",
        "hpi2000",
        "source_type",
    ]

    def __init__(self, driver: Driver, batch_size: int = 10000) -> None:
        """Initialize HPISnapshot loader.

        Args:
            driver: Neo4j driver instance.
            batch_size: Number of records per batch (default: 10000).
        """
        super().__init__(driver, "HPISnapshot", "snapshot_id", batch_size)

    def load_from_parquet(self, parquet_path: str, dry_run: bool = False) -> int:
        """Load HPISnapshot nodes from parquet file.

        Args:
            parquet_path: Path to tract_hpi_enriched.parquet file.
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
        self.logger.info(f"Loaded {len(df)} HPISnapshot records from {parquet_path}")
        self.validate_schema(df, self.REQUIRED_COLUMNS, parquet_path)

        if dry_run:
            self.logger.info(f"Dry-run: verified schema for {len(df)} HPISnapshot records")
            return len(df)

        merge_cypher = """
        UNWIND $batch AS row
        MERGE (h:HPISnapshot {snapshot_id: row.snapshot_id})
        ON CREATE SET
            h.tract_fips = row.tract_fips,
            h.county_fips = row.county_fips,
            h.state_fips = row.state_fips,
            h.year = row.year,
            h.hpi = row.hpi,
            h.annual_change = row.annual_change,
            h.hpi1990 = row.hpi1990,
            h.hpi2000 = row.hpi2000,
            h.source_type = row.source_type
        ON MATCH SET
            h.tract_fips = COALESCE(row.tract_fips, h.tract_fips),
            h.county_fips = COALESCE(row.county_fips, h.county_fips),
            h.state_fips = COALESCE(row.state_fips, h.state_fips),
            h.year = COALESCE(row.year, h.year),
            h.hpi = COALESCE(row.hpi, h.hpi),
            h.annual_change = COALESCE(row.annual_change, h.annual_change),
            h.hpi1990 = COALESCE(row.hpi1990, h.hpi1990),
            h.hpi2000 = COALESCE(row.hpi2000, h.hpi2000),
            h.source_type = COALESCE(row.source_type, h.source_type)
        """

        total_records = len(df)
        for batch_index in range(0, total_records, self.batch_size):
            batch_df = df.iloc[batch_index : batch_index + self.batch_size]
            records = self._prepare_batch(batch_df)
            self.logger.debug(
                f"Processing batch {batch_index // self.batch_size + 1} ({len(records)} records, {batch_index}/{total_records})"
            )
            self.execute_batch(merge_cypher, records)
            if (batch_index // self.batch_size + 1) % 100 == 0:
                self.logger.info(
                    f"Processed batch {batch_index // self.batch_size + 1} "
                    f"(estimated records: {batch_index + len(records)}/{total_records})"
                )

        final_count = self.get_node_count()
        self.logger.info(f"HPISnapshot load complete. Total nodes: {final_count}")
        return final_count


def main() -> None:
    """Run HPISnapshot loader from the command line."""
    run_loader_from_cli(
        HPISnapshotLoader,
        "data/gold/fhfa/tract_hpi_enriched.parquet",
        "Load HPISnapshot nodes into Neo4j",
        10000,
    )


if __name__ == "__main__":
    main()
