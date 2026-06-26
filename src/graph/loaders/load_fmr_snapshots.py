"""Loader for FMRSnapshot nodes."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from neo4j import Driver

from .base_loader import BaseLoader, run_loader_from_cli


class FMRSnapshotLoader(BaseLoader):
    """Loader for graph-ready HUD FMRSnapshot records."""

    REQUIRED_COLUMNS: ClassVar[list[str]] = [
        "snapshot_id",
        "county_fips",
        "state_fips",
        "year",
        "studio_rent",
        "one_bedroom_rent",
        "two_bedroom_rent",
        "three_bedroom_rent",
        "four_bedroom_rent",
        "hud_area_code",
        "hud_area_name",
        "source_type",
    ]

    def __init__(self, driver: Driver, batch_size: int = 5000) -> None:
        """Initialize FMRSnapshot loader."""
        super().__init__(driver, "FMRSnapshot", "snapshot_id", batch_size)

    def load_from_parquet(self, parquet_path: str, dry_run: bool = False) -> int:
        """Load FMRSnapshot nodes from parquet."""
        path = Path(parquet_path)
        if not path.exists():
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

        df = pd.read_parquet(path)
        self.logger.info("Loaded %s FMRSnapshot records from %s", len(df), parquet_path)
        self.validate_schema(df, self.REQUIRED_COLUMNS, parquet_path)

        if dry_run:
            self.logger.info("Dry-run: verified schema for %s FMRSnapshot records", len(df))
            return len(df)

        merge_cypher = """
        UNWIND $batch AS row
        MERGE (f:FMRSnapshot {snapshot_id: row.snapshot_id})
        ON CREATE SET
            f.county_fips = row.county_fips,
            f.state_fips = row.state_fips,
            f.year = row.year,
            f.studio_rent = row.studio_rent,
            f.one_bedroom_rent = row.one_bedroom_rent,
            f.two_bedroom_rent = row.two_bedroom_rent,
            f.three_bedroom_rent = row.three_bedroom_rent,
            f.four_bedroom_rent = row.four_bedroom_rent,
            f.hud_area_code = row.hud_area_code,
            f.hud_area_name = row.hud_area_name,
            f.source_type = row.source_type
        ON MATCH SET
            f.county_fips = COALESCE(row.county_fips, f.county_fips),
            f.state_fips = COALESCE(row.state_fips, f.state_fips),
            f.year = COALESCE(row.year, f.year),
            f.studio_rent = COALESCE(row.studio_rent, f.studio_rent),
            f.one_bedroom_rent = COALESCE(row.one_bedroom_rent, f.one_bedroom_rent),
            f.two_bedroom_rent = COALESCE(row.two_bedroom_rent, f.two_bedroom_rent),
            f.three_bedroom_rent = COALESCE(row.three_bedroom_rent, f.three_bedroom_rent),
            f.four_bedroom_rent = COALESCE(row.four_bedroom_rent, f.four_bedroom_rent),
            f.hud_area_code = COALESCE(row.hud_area_code, f.hud_area_code),
            f.hud_area_name = COALESCE(row.hud_area_name, f.hud_area_name),
            f.source_type = COALESCE(row.source_type, f.source_type)
        """

        total_records = len(df)
        for batch_index in range(0, total_records, self.batch_size):
            batch_df = df.iloc[batch_index : batch_index + self.batch_size]
            records = self._prepare_batch(batch_df)
            self.execute_batch(merge_cypher, records)
            self.logger.info(
                "Completed FMRSnapshot batch %s (%s/%s)",
                batch_index // self.batch_size + 1,
                min(batch_index + self.batch_size, total_records),
                total_records,
            )

        final_count = self.get_node_count()
        self.logger.info("FMRSnapshot load complete. Total nodes: %s", final_count)
        return final_count


def main() -> None:
    """Run FMRSnapshot loader from the command line."""
    run_loader_from_cli(
        FMRSnapshotLoader,
        "data/gold/hud/fmr_snapshots.parquet",
        "Load FMRSnapshot nodes into Neo4j",
        5000,
    )


if __name__ == "__main__":
    main()

