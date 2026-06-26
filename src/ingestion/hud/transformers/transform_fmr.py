"""Transform Bronze HUD standard FMR workbooks into normalized Silver parquet."""

from __future__ import annotations

import argparse
from pathlib import Path
import re

import pandas as pd

from src.ingestion.hud.excel_utils import iter_repaired_excel_path


REQUESTED_INPUT_DIR = Path("data/bronze/hud/fmr")
FALLBACK_INPUT_DIR = Path("data/bronze/fmr")
OUTPUT_PATH = Path("data/silver/hud/fmr.parquet")

SILVER_COLUMNS = [
    "fiscal_year",
    "fmr_snapshot_id",
    "fips10",
    "state_fips",
    "county_fips",
    "hud_area_code",
    "hud_area_name",
    "county_name",
    "county_town_name",
    "state_abbr",
    "is_metro",
    "population",
    "fmr_0br",
    "fmr_1br",
    "fmr_2br",
    "fmr_3br",
    "fmr_4br",
    "source_type",
    "source_file",
]


def transform_fmr(
    input_dir: Path = REQUESTED_INPUT_DIR,
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    """Normalize all standard FMR Bronze workbooks into one Silver parquet."""
    source_dir = _resolve_input_dir(input_dir)
    files = _fmr_files(source_dir)
    if not files:
        raise FileNotFoundError(f"No standard FMR workbooks found in {source_dir}")

    frames = [_transform_file(path) for path in files]
    combined = pd.concat(frames, ignore_index=True)
    combined = _select_county_year_snapshots(combined)
    _validate_silver(combined)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output_path, index=False)
    print(f"Rows: {len(combined)}")
    print(f"Columns: {len(combined.columns)}")
    print(f"Fiscal years: {combined['fiscal_year'].min()}-{combined['fiscal_year'].max()}")
    print(f"Saved Silver HUD FMR parquet to {output_path}")
    return combined


def _transform_file(path: Path) -> pd.DataFrame:
    fiscal_year = _extract_fiscal_year(path)
    with iter_repaired_excel_path(path) as readable_path:
        with pd.ExcelFile(readable_path) as excel:
            sheet_name = _data_sheet(excel.sheet_names)
            df = pd.read_excel(excel, sheet_name=sheet_name, dtype=object).dropna(how="all")

    df = _standardize_columns(df)
    fips_col = _require_first(df, ["fips", "fips2010"], path)
    hud_code_col = _require_first(df, ["hud_area_code", "metro_code"], path)
    hud_name_col = _require_first(df, ["hud_area_name", "areaname"], path)
    population_col = _first_present(df, ["pop2023", "pop2022", "pop2020", "pop2017", "pop2010"])

    out = pd.DataFrame()
    out["fiscal_year"] = pd.Series(fiscal_year, index=df.index, dtype="Int64")
    out["fips10"] = df[fips_col].map(_format_code_10)
    out["state_fips"] = out["fips10"].str[:2]
    out["county_fips"] = out["fips10"].str[:5]
    out["hud_area_code"] = df[hud_code_col].map(_clean_string)
    out["hud_area_name"] = df[hud_name_col].map(_clean_string)
    out["county_name"] = df["countyname"].map(_clean_string) if "countyname" in df else pd.NA
    out["county_town_name"] = (
        df["county_town_name"].map(_clean_string) if "county_town_name" in df else pd.NA
    )
    out["state_abbr"] = _state_abbr(df)
    out["is_metro"] = df["metro"].map(_to_bool) if "metro" in df else pd.NA
    out["population"] = (
        pd.to_numeric(df[population_col], errors="coerce").astype("Int64")
        if population_col
        else pd.Series(pd.NA, index=df.index, dtype="Int64")
    )
    for source_col, target_col in {
        "fmr_0": "fmr_0br",
        "fmr_1": "fmr_1br",
        "fmr_2": "fmr_2br",
        "fmr_3": "fmr_3br",
        "fmr_4": "fmr_4br",
    }.items():
        if source_col not in df:
            raise ValueError(f"Missing required rent column {source_col} in {path}")
        out[target_col] = pd.to_numeric(df[source_col], errors="coerce").astype("Int64")
    out["source_type"] = "HUD_FMR"
    out["source_file"] = str(path)
    out["_county_level_rank"] = out["fips10"].str.endswith("99999").map(lambda value: 0 if value else 1)
    out = out.sort_values(["fiscal_year", "county_fips", "_county_level_rank", "fips10"])
    out["fmr_snapshot_id"] = out["county_fips"].astype(str) + "_" + out["fiscal_year"].astype(str)
    return out


def _select_county_year_snapshots(df: pd.DataFrame) -> pd.DataFrame:
    selected = (
        df.sort_values(["fiscal_year", "county_fips", "_county_level_rank", "fips10"])
        .drop_duplicates(subset=["county_fips", "fiscal_year"], keep="first")
        .drop(columns=["_county_level_rank"])
        .reset_index(drop=True)
    )
    return selected[SILVER_COLUMNS]


def _validate_silver(df: pd.DataFrame) -> None:
    missing = [column for column in SILVER_COLUMNS if column not in df.columns]
    if missing:
        raise RuntimeError(f"Missing Silver FMR columns: {missing}")
    if not df["county_fips"].astype(str).str.match(r"^\d{5}$").all():
        raise RuntimeError("county_fips must be exactly 5 digits")
    if not df["state_fips"].astype(str).str.match(r"^\d{2}$").all():
        raise RuntimeError("state_fips must be exactly 2 digits")
    rent_columns = ["fmr_0br", "fmr_1br", "fmr_2br", "fmr_3br", "fmr_4br"]
    if df[rent_columns].isna().any().any():
        raise RuntimeError("FMR rent columns must not contain null values")
    if (df[rent_columns] < 0).any().any():
        raise RuntimeError("FMR rent columns must be non-negative")
    duplicates = df.duplicated(subset=["county_fips", "fiscal_year"], keep=False)
    if duplicates.any():
        raise RuntimeError("Uniqueness validation failed for county_fips + fiscal_year")


def _resolve_input_dir(input_dir: Path) -> Path:
    if input_dir.exists():
        return input_dir
    if input_dir == REQUESTED_INPUT_DIR and FALLBACK_INPUT_DIR.exists():
        return FALLBACK_INPUT_DIR
    raise FileNotFoundError(f"FMR Bronze directory not found: {input_dir}")


def _fmr_files(input_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(input_dir.glob("*.xlsx"))
        if "fmr" in path.name.lower()
        and "safmr" not in path.name.lower()
        and "erap" not in path.name.lower()
    ]


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [re.sub(r"[^0-9a-zA-Z]+", "_", str(column)).strip("_").lower() for column in df.columns]
    return df


def _require_first(df: pd.DataFrame, columns: list[str], path: Path) -> str:
    column = _first_present(df, columns)
    if column is None:
        raise ValueError(f"Missing required columns {columns} in {path}")
    return column


def _first_present(df: pd.DataFrame, columns: list[str]) -> str | None:
    return next((column for column in columns if column in df.columns), None)


def _format_code_10(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(10) if text.isdigit() else text


def _clean_string(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _state_abbr(df: pd.DataFrame) -> pd.Series:
    for column in ["state_alpha", "stusps"]:
        if column in df:
            return df[column].map(_clean_string)
    return pd.Series(pd.NA, index=df.index, dtype="string")


def _to_bool(value: object) -> bool | None:
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


def _extract_fiscal_year(path: Path) -> int:
    name = path.name.lower()
    match = re.search(r"fy(?:20)?(\d{2})", name)
    if match:
        return 2000 + int(match.group(1))
    match = re.search(r"fmr(20\d{2})", name)
    if match:
        return int(match.group(1))
    raise ValueError(f"Could not derive fiscal year from filename: {path.name}")


def _data_sheet(sheet_names: list[str]) -> str:
    for sheet_name in sheet_names:
        if "field" not in sheet_name.lower():
            return sheet_name
    raise ValueError("Workbook does not contain a data sheet")


def main() -> None:
    """Run Silver HUD FMR transformation from the command line."""
    parser = argparse.ArgumentParser(description="Transform Bronze HUD FMR workbooks to Silver")
    parser.add_argument("--input-dir", default=str(REQUESTED_INPUT_DIR))
    parser.add_argument("--output-path", default=str(OUTPUT_PATH))
    args = parser.parse_args()
    transform_fmr(Path(args.input_dir), Path(args.output_path))


if __name__ == "__main__":
    main()
