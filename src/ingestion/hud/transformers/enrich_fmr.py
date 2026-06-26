"""Create graph-ready Gold FMRSnapshot records from Silver HUD FMR."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/silver/hud/fmr.parquet")
OUTPUT_PATH = Path("data/gold/hud/fmr_snapshots.parquet")

GOLD_COLUMNS = [
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


def enrich_fmr(
    input_path: Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    """Transform Silver FMR records into graph-ready Gold records."""
    if not input_path.exists():
        raise FileNotFoundError(f"Silver FMR parquet not found: {input_path}")

    silver = pd.read_parquet(input_path)
    required = [
        "fmr_snapshot_id",
        "county_fips",
        "state_fips",
        "fiscal_year",
        "fmr_0br",
        "fmr_1br",
        "fmr_2br",
        "fmr_3br",
        "fmr_4br",
        "hud_area_code",
        "hud_area_name",
        "source_type",
    ]
    missing = [column for column in required if column not in silver.columns]
    if missing:
        raise RuntimeError(f"Missing required Silver FMR columns: {missing}")

    gold = pd.DataFrame(
        {
            "snapshot_id": silver["fmr_snapshot_id"],
            "county_fips": silver["county_fips"],
            "state_fips": silver["state_fips"],
            "year": silver["fiscal_year"].astype("Int64"),
            "studio_rent": silver["fmr_0br"].astype("Int64"),
            "one_bedroom_rent": silver["fmr_1br"].astype("Int64"),
            "two_bedroom_rent": silver["fmr_2br"].astype("Int64"),
            "three_bedroom_rent": silver["fmr_3br"].astype("Int64"),
            "four_bedroom_rent": silver["fmr_4br"].astype("Int64"),
            "hud_area_code": silver["hud_area_code"],
            "hud_area_name": silver["hud_area_name"],
            "source_type": silver["source_type"],
        }
    )
    _validate_gold(gold)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gold.to_parquet(output_path, index=False)
    print(f"Rows: {len(gold)}")
    print(f"Columns: {len(gold.columns)}")
    print(f"Saved Gold HUD FMR parquet to {output_path}")
    return gold


def _validate_gold(df: pd.DataFrame) -> None:
    missing = [column for column in GOLD_COLUMNS if column not in df.columns]
    if missing:
        raise RuntimeError(f"Missing Gold FMR columns: {missing}")
    null_required = df[GOLD_COLUMNS].isna().sum()
    bad_nulls = null_required[null_required > 0]
    if not bad_nulls.empty:
        raise RuntimeError(f"Gold FMR null check failed: {bad_nulls.to_dict()}")
    if df["snapshot_id"].duplicated().any():
        raise RuntimeError("Gold FMR snapshot_id values must be unique")
    expected = df["county_fips"].astype(str) + "_" + df["year"].astype(str)
    if not (df["snapshot_id"].astype(str) == expected).all():
        raise RuntimeError("Gold FMR business key integrity check failed")
    if not df["county_fips"].astype(str).str.match(r"^\d{5}$").all():
        raise RuntimeError("Gold FMR county_fips must be exactly 5 digits")
    if not df["state_fips"].astype(str).str.match(r"^\d{2}$").all():
        raise RuntimeError("Gold FMR state_fips must be exactly 2 digits")


def main() -> None:
    """Run Gold HUD FMR enrichment from the command line."""
    parser = argparse.ArgumentParser(description="Enrich Silver HUD FMR into Gold FMRSnapshot records")
    parser.add_argument("--input-path", default=str(INPUT_PATH))
    parser.add_argument("--output-path", default=str(OUTPUT_PATH))
    args = parser.parse_args()
    enrich_fmr(Path(args.input_path), Path(args.output_path))


if __name__ == "__main__":
    main()

