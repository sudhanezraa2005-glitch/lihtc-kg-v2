from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

import pandas as pd

INPUT_CSV = Path("data/raw/fhfa/tract_hpi/hpi_at_tract.csv")
OUTPUT_PARQUET = Path("data/silver/fhfa/tract_hpi.parquet")

# mapping from normalized column name to canonical name
RENAME_MAP = {
    # tract
    "tract": "tract",
    "tract_id": "tract",
    "tract code": "tract",
    "tractcode": "tract",
    # state abbreviation
    "state_abbr": "state_abbr",
    "stateabbr": "state_abbr",
    "state": "state_abbr",
    "state code": "state_abbr",
    # year
    "year": "year",
    "yr": "year",
    # annual change
    "annual_change": "annual_change",
    "annual change": "annual_change",
    "annualpercentchange": "annual_change",
    "annual_pct_change": "annual_change",
    # hpi
    "hpi": "hpi",
    "hpi_index": "hpi",
    # hpi1990
    "hpi1990": "hpi1990",
    "hpi_1990": "hpi1990",
    # hpi2000
    "hpi2000": "hpi2000",
    "hpi_2000": "hpi2000",
}

REQUIRED_COLUMNS = ["tract", "state_abbr", "year", "annual_change", "hpi", "hpi1990", "hpi2000"]


def _normalize(col: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", col).strip("_").lower()


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        norm = _normalize(col)
        if norm in RENAME_MAP:
            rename[col] = RENAME_MAP[norm]
        else:
            # try without underscores
            collapsed = norm.replace("_", "")
            if collapsed in RENAME_MAP:
                rename[col] = RENAME_MAP[collapsed]
    if rename:
        df = df.rename(columns=rename)
    return df


def transform_tract_hpi(input_csv: Path = INPUT_CSV, output_parquet: Path = OUTPUT_PARQUET) -> pd.DataFrame:
    df = _read_csv(input_csv)
    df = _standardize_columns(df)

    # validate required columns present
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required columns: {missing}")

    # convert dtypes
    df["tract"] = df["tract"].astype(str).str.strip()
    df["state_abbr"] = df["state_abbr"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["annual_change"] = pd.to_numeric(df["annual_change"], errors="coerce")
    df["hpi"] = pd.to_numeric(df["hpi"], errors="coerce")
    df["hpi1990"] = pd.to_numeric(df["hpi1990"], errors="coerce")
    df["hpi2000"] = pd.to_numeric(df["hpi2000"], errors="coerce")

    # create business key
    df["tract_year_key"] = df["tract"].astype(str) + "_" + df["year"].astype(str)

    # validate uniqueness of tract + year
    duplicates_bool = df.duplicated(subset=["tract", "year"], keep=False)
    duplicate_count = int(duplicates_bool.sum())
    if duplicate_count > 0:
        print(f"Duplicate rows for tract+year: {duplicate_count}")
        dup_sample = df[duplicates_bool].head(20)[["tract", "year", "tract_year_key"]]
        print("Sample duplicates:")
        print(dup_sample)
        raise RuntimeError("Uniqueness validation failed for tract + year")

    # save parquet
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, index=False)

    # print requested stats
    row_count = int(df.shape[0])
    column_count = int(df.shape[1])
    unique_tract_count = int(df["tract"].nunique(dropna=True))
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())

    print(f"Rows: {row_count}")
    print(f"Columns: {column_count}")
    print(f"Duplicate count (tract+year): {duplicate_count}")
    print(f"Unique tract count: {unique_tract_count}")
    print(f"Min year: {min_year}")
    print(f"Max year: {max_year}")

    return df


def main() -> None:
    transform_tract_hpi()


if __name__ == "__main__":
    main()
