from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from .utils import read_csv_all_str, save_parquet, profile_df_to_json

RAW_CSV = Path("data/raw/geography/census_tract_reference_2025.csv")
OUTPUT_PARQUET = Path("data/silver/geography/tract_reference.parquet")
PROFILE_JSON = Path("metadata/profiling/geography_profile.json")

RENAME_MAP = {
    "GEOID": "tract_fips",
    "STATEFP": "state_fips",
    "COUNTYFP": "county_code",
    "TRACTCE": "tract_code",
    "NAME": "tract_name",
}


def transform_geography_reference(input_csv: Path = RAW_CSV, output_parquet: Path = OUTPUT_PARQUET, profile_json: Path = PROFILE_JSON) -> pd.DataFrame:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = read_csv_all_str(input_csv)

    # rename columns if present
    rename = {c: RENAME_MAP[c] for c in RENAME_MAP.keys() if c in df.columns}
    if rename:
        df = df.rename(columns=rename)

    # Ensure required canonical columns exist (create with NA if missing)
    for col in ["tract_fips", "state_fips", "county_code", "tract_code", "tract_name"]:
        if col not in df.columns:
            df[col] = pd.NA

    # Strip whitespace on string-like columns (avoid DataFrame.applymap compatibility issues)
    for c in df.columns:
        try:
            if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object:
                df[c] = df[c].astype(str).str.strip()
                df[c] = df[c].replace({"": pd.NA, "nan": pd.NA})
        except Exception:
            # fallback: leave column as-is
            pass

    # zero-pad state_fips to 2 and county_code to 3 where numeric-like
    def zpad(s, width):
        if pd.isna(s):
            return pd.NA
        try:
            return str(int(s)).zfill(width)
        except Exception:
            s2 = str(s).strip()
            return s2.zfill(width) if s2.isdigit() else s2

    df["state_fips"] = df["state_fips"].apply(lambda v: zpad(v, 2))
    df["county_code"] = df["county_code"].apply(lambda v: zpad(v, 3))

    # create county_fips
    df["county_fips"] = df.apply(lambda r: (r["state_fips"] or "") + (r["county_code"] or ""), axis=1)

    # validations
    # tract_fips unique
    if df["tract_fips"].isna().any():
        missing = df[df["tract_fips"].isna()].head(5)
        print("Error: Some rows missing tract_fips. Sample:", file=sys.stderr)
        print(missing, file=sys.stderr)
        raise RuntimeError("Missing tract_fips values")

    dup = df[df.duplicated(subset=["tract_fips"], keep=False)]
    if not dup.empty:
        print(f"Error: Duplicate tract_fips found: {dup.shape[0]} rows. Sample:", file=sys.stderr)
        print(dup.head(10), file=sys.stderr)
        raise RuntimeError("Duplicate tract_fips values")

    # state_fips not null
    if df["state_fips"].isna().any() or (df["state_fips"].astype(str).str.strip() == "").any():
        bad = df[df["state_fips"].isna() | (df["state_fips"].astype(str).str.strip() == "")].head(5)
        print("Error: Missing state_fips. Sample:", file=sys.stderr)
        print(bad, file=sys.stderr)
        raise RuntimeError("Missing state_fips values")

    # county_fips not null
    if df["county_fips"].isna().any() or (df["county_fips"].astype(str).str.strip() == "").any():
        bad = df[df["county_fips"].isna() | (df["county_fips"].astype(str).str.strip() == "")].head(5)
        print("Error: Missing county_fips. Sample:", file=sys.stderr)
        print(bad, file=sys.stderr)
        raise RuntimeError("Missing county_fips values")

    # save parquet
    save_parquet(df, output_parquet)

    # profile
    profile_df_to_json(df, profile_json)

    print(f"Saved geography reference to {output_parquet} (rows={df.shape[0]})")
    return df


if __name__ == "__main__":
    transform_geography_reference()
