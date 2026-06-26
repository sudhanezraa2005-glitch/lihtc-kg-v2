"""Build Gold tract-level ACS snapshot parquet."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.ingestion.acs.registry import enabled_tables, load_registry


OUTPUT_PATH = Path("data/gold/acs/tract_acs_snapshot.parquet")


def build_tract_acs_snapshot(
    registry_path: Path = Path("metadata/acs/table_registry.yaml"),
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    """Build a single Gold tract ACS snapshot from enabled Silver tables."""
    registry = load_registry(registry_path)
    frames: list[pd.DataFrame] = []
    for table in enabled_tables(registry):
        table_config = registry["tables"][table]
        silver_path = Path(table_config["silver_output"])
        if not silver_path.exists():
            raise FileNotFoundError(f"Silver ACS parquet not found: {silver_path}")
        frames.append(pd.read_parquet(silver_path))
    if not frames:
        raise RuntimeError("No enabled ACS Silver tables configured")

    gold = frames[0]
    for frame in frames[1:]:
        gold = gold.merge(frame, on=["tract_fips", "state_fips", "county_fips", "year"], how="outer")
    gold["snapshot_id"] = gold["tract_fips"].astype(str) + "_" + gold["year"].astype(str)
    columns = ["snapshot_id", "tract_fips", "county_fips", "state_fips", "year", *registry["gold"]["enabled_fields"]]
    
    missing = [
    c for c in registry["gold"]["enabled_fields"]
    if c not in gold.columns
]

    if missing:
        raise RuntimeError(
            f"Gold ACS fields missing after merge: {missing}"
    )
    gold = gold[columns]
    _validate_gold(gold)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gold.to_parquet(output_path, index=False)
    print(f"Saved Gold ACS snapshot rows={len(gold)} to {output_path}")
    return gold


def _validate_gold(df: pd.DataFrame) -> None:
    if df["snapshot_id"].duplicated().any():
        raise RuntimeError("Gold ACS snapshot_id must be unique")
    if not df["tract_fips"].astype(str).str.match(r"^\d{11}$").all():
        raise RuntimeError("Gold ACS tract_fips must be exactly 11 digits")
    if df[["snapshot_id", "tract_fips", "county_fips", "state_fips", "year"]].isna().any().any():
        raise RuntimeError("Gold ACS key columns must not be null")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Gold tract ACS snapshot")
    parser.add_argument("--registry", default="metadata/acs/table_registry.yaml")
    parser.add_argument("--output-path", default=str(OUTPUT_PATH))
    args = parser.parse_args()
    build_tract_acs_snapshot(Path(args.registry), Path(args.output_path))


if __name__ == "__main__":
    main()

