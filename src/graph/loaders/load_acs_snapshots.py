"""Loader for ACSSnapshot nodes."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from neo4j import Driver

from .base_loader import BaseLoader, run_loader_from_cli


class ACSSnapshotLoader(BaseLoader):
    """Loader for ACSSnapshot nodes."""

    REQUIRED_COLUMNS: ClassVar[list[str]] = [
        "snapshot_id",
        "tract_fips",
        "county_fips",
        "state_fips",
        "year",
    ]

    def __init__(
        self,
        driver: Driver,
        batch_size: int = 10000,
    ) -> None:
        super().__init__(
            driver,
            "ACSSnapshot",
            "snapshot_id",
            batch_size,
        )

    def load_from_parquet(
        self,
        parquet_path: str,
        dry_run: bool = False,
    ) -> int:

        path = Path(parquet_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Parquet file not found: {parquet_path}"
            )

        df = pd.read_parquet(path)

        self.logger.info(
            "Loaded %s ACSSnapshot records from %s",
            len(df),
            parquet_path,
        )

        self.validate_schema(
            df,
            self.REQUIRED_COLUMNS,
            parquet_path,
        )

        if dry_run:
            self.logger.info(
                "Dry-run: verified schema for %s ACSSnapshot records",
                len(df),
            )
            return len(df)

        merge_cypher = """
        UNWIND $batch AS row

        MERGE (a:ACSSnapshot {
            snapshot_id: row.snapshot_id
        })

        SET a += row
        """

        total_records = len(df)

        for batch_index in range(
            0,
            total_records,
            self.batch_size,
        ):
            batch_df = df.iloc[
                batch_index : batch_index + self.batch_size
            ]

            records = self._prepare_batch(batch_df)

            self.execute_batch(
                merge_cypher,
                records,
            )

            if (batch_index // self.batch_size + 1) % 20 == 0:
                self.logger.info(
                    "Processed %s/%s records",
                    min(
                        batch_index + self.batch_size,
                        total_records,
                    ),
                    total_records,
                )

        final_count = self.get_node_count()

        self.logger.info(
            "ACSSnapshot load complete. Total nodes: %s",
            final_count,
        )

        return final_count


def main() -> None:
    run_loader_from_cli(
        ACSSnapshotLoader,
        "data/gold/acs/tract_acs_snapshot.parquet",
        "Load ACSSnapshot nodes into Neo4j",
        10000,
    )


if __name__ == "__main__":
    main()