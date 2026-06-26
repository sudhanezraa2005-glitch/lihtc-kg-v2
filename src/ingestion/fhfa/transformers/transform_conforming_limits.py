from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pandas as pd

INPUT_DIR = Path("data/raw/fhfa/conforming_limits")
OUTPUT_PATH = Path("data/silver/fhfa/conforming_limits.parquet")

# mapping of normalized column names to standardized names
COLUMN_MAPPING = {
    "fips_state_code": "state_fips",
    "fips state code": "state_fips",
    "fips_state_code": "state_fips",
    "fips_county_code": "county_code",
    "fips county code": "county_code",
    "county_name": "county_name",
    "county name": "county_name",
    "cbsa_number": "cbsa_number",
    "cbsa number": "cbsa_number",
    "one_unit_limit": "limit_1_unit",
    "one-unit limit": "limit_1_unit",
    "one-unit\nlimit": "limit_1_unit",
    "two_unit_limit": "limit_2_unit",
    "two-unit limit": "limit_2_unit",
    "three_unit_limit": "limit_3_unit",
    "three-unit limit": "limit_3_unit",
    "four_unit_limit": "limit_4_unit",
    "four-unit limit": "limit_4_unit",
}


def _normalize_col(col: str) -> str:
    # lowercase, replace non-alphanumeric with space, collapse spaces
    s = re.sub(r"[^0-9a-zA-Z]+", " ", str(col)).strip().lower()
    return s


def _read_file(path: Path) -> pd.DataFrame:
    suf = path.suffix.lower()
    if suf == ".csv":
        return pd.read_csv(path)
    if suf in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {suf}")


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        norm = _normalize_col(col)
        # try exact mapping
        if norm in COLUMN_MAPPING:
            rename_map[col] = COLUMN_MAPPING[norm]
        else:
            # try replacing underscores/space variants
            key = norm.replace(" ", "_")
            if key in COLUMN_MAPPING:
                rename_map[col] = COLUMN_MAPPING[key]
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def _extract_year_from_filename(path: Path) -> int | None:
    m = re.search(r"(20\d{2})", path.name)
    if m:
        return int(m.group(1))
    return None


def _format_fips_part(val, width: int) -> str:
    if pd.isna(val):
        return ""
    try:
        iv = int(val)
        return str(iv).zfill(width)
    except Exception:
        s = str(val).strip()
        return s.zfill(width) if s.isdigit() else s


def transform_and_combine(input_dir: Path = INPUT_DIR, output_path: Path = OUTPUT_PATH) -> pd.DataFrame:
    input_dir = Path(input_dir)
    files: List[Path] = []
    if input_dir.exists():
        for p in sorted(input_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in {".csv", ".xls", ".xlsx"}:
                files.append(p)

    frames = []
    for p in files:
        df = _read_file(p)
        df = _standardize_columns(df)
        year = _extract_year_from_filename(p)
        if year is None:
            # if not in filename, try common columns
            for col in ["year", "Year", "YEAR"]:
                if col in df.columns:
                    year = int(df[col].dropna().astype(int).iloc[0])
                    break
        df["year"] = year

        # ensure expected standardized columns exist (fill missing)
        for needed in ["state_fips", "county_code", "county_name"]:
            if needed not in df.columns:
                df[needed] = pd.NA

        # create county_fips
        df["state_fips"] = df["state_fips"].replace("", pd.NA)
        df["county_code"] = df["county_code"].replace("", pd.NA)
        df["county_fips"] = df.apply(lambda r: _format_fips_part(r["state_fips"], 2) + _format_fips_part(r["county_code"], 3), axis=1)

        # coerce loan limit columns to numeric if present
        for col in ["limit_1_unit", "limit_2_unit", "limit_3_unit", "limit_4_unit"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

        frames.append(df)

    if not frames:
        combined = pd.DataFrame()
    else:
        combined = pd.concat(frames, ignore_index=True, sort=False)

    # ensure output dir
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # save parquet
    combined.to_parquet(output_path, index=False)

    # validate uniqueness of county_fips + year
    if not combined.empty:
        dup = combined[combined.duplicated(subset=["county_fips", "year"], keep=False)]
        if not dup.empty:
            # print some duplicates and raise
            sample = dup.head(20)
            print(f"Found {dup.shape[0]} duplicate rows for county_fips+year. Sample:")
            print(sample[["county_fips", "year"] + [c for c in ["county_name", "state_fips", "county_code"] if c in sample.columns]].drop_duplicates())
            raise RuntimeError("Uniqueness validation failed for county_fips + year")
        else:
            print(f"Uniqueness validated: county_fips + year is unique across {combined.shape[0]} rows.")

    print(f"Saved combined Parquet to {output_path}")
    return combined


def main() -> None:
    transform_and_combine()


if __name__ == "__main__":
    main()
