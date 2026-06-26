from __future__ import annotations

from pathlib import Path

import pandas as pd

from .utils import save_parquet

TRACT_HPI_PARQUET = Path("data/silver/fhfa/tract_hpi.parquet")
TRACT_REF_PARQUET = Path("data/silver/geography/tract_reference.parquet")
OUTPUT_PARQUET = Path("data/gold/fhfa/tract_hpi_enriched.parquet")

OUTPUT_COLUMNS = [
    "tract_fips",
    "county_fips",
    "state_fips",
    "year",
    "hpi",
    "annual_change",
    "hpi1990",
    "hpi2000",
]


def enrich_tract_hpi(tract_hpi_path: Path = TRACT_HPI_PARQUET, tract_ref_path: Path = TRACT_REF_PARQUET, output_path: Path = OUTPUT_PARQUET) -> pd.DataFrame:
    df_hpi = pd.read_parquet(tract_hpi_path)
    df_ref = pd.read_parquet(tract_ref_path)

    # normalize FHFA tract ID to tract_fips for join compatibility
    df_hpi = df_hpi.copy()
    df_hpi["tract_fips"] = df_hpi["tract"].astype(str).str.zfill(11)

    # merge
    merged = df_hpi.merge(
        df_ref[["tract_fips", "county_fips", "state_fips"]],
        on="tract_fips",
        how="left",
        validate="m:1",
    )

    # prepare output frame
    out = pd.DataFrame()
    out["tract_fips"] = merged["tract_fips"]
    out["county_fips"] = merged["county_fips"]
    out["state_fips"] = merged["state_fips"]
    out["year"] = merged["year"]
    out["hpi"] = merged.get("hpi")
    out["annual_change"] = merged.get("annual_change")
    out["hpi1990"] = merged.get("hpi1990")
    out["hpi2000"] = merged.get("hpi2000")

    # save
    save_parquet(out, output_path)

    total_rows = int(out.shape[0])
    unmatched = int(out["county_fips"].isna().sum())
    match_rate = 1.0 - (unmatched / total_rows if total_rows else 0.0)
    duplicate_count = int(out.duplicated(subset=["tract_fips", "year"]).sum())

    print(f"Enriched rows: {total_rows}")
    print(f"Unmatched tract count: {unmatched}")
    print(f"Match rate: {match_rate:.6f}")
    print(f"Duplicate count (tract_fips+year): {duplicate_count}")

    if match_rate < 1.0:
        raise RuntimeError(f"Track join match rate below 100%: {match_rate:.6f}")

    return out


if __name__ == "__main__":
    enrich_tract_hpi()
