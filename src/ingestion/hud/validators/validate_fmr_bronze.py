"""Validate Bronze HUD standard FMR workbooks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import re

import pandas as pd

from src.ingestion.hud.excel_utils import iter_repaired_excel_path


REQUESTED_INPUT_DIR = Path("data/bronze/hud/fmr")
FALLBACK_INPUT_DIR = Path("data/bronze/fmr")
DEFAULT_REPORT_PATH = Path("metadata/hud_fmr/fmr_bronze_validation_summary.md")

RENT_COLUMNS = ["fmr_0", "fmr_1", "fmr_2", "fmr_3", "fmr_4"]
REQUIRED_CONCEPTS = {
    "fips": {"fips", "fips2010"},
    "hud_area_code": {"hud_area_code", "metro_code"},
    "hud_area_name": {"hud_area_name", "areaname"},
    "county_name": {"countyname"},
    "metro": {"metro"},
    "state": {"state"},
}


@dataclass(frozen=True)
class BronzeFMRFileValidation:
    """Validation result for one Bronze FMR workbook."""

    file_path: str
    fiscal_year: int
    sheet_name: str
    row_count: int
    column_count: int
    missing_required_concepts: list[str]
    malformed_fips_count: int
    malformed_hud_area_code_count: int
    duplicate_fips10_count: int
    null_rent_count: int
    schema_signature: str

    @property
    def is_valid(self) -> bool:
        return (
            not self.missing_required_concepts
            and self.malformed_fips_count == 0
            and self.malformed_hud_area_code_count == 0
            and self.duplicate_fips10_count == 0
            and self.null_rent_count == 0
        )


def validate_fmr_bronze(
    input_dir: Path = REQUESTED_INPUT_DIR,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> list[BronzeFMRFileValidation]:
    """Validate all standard FMR workbooks and write a Markdown summary."""
    source_dir = _resolve_input_dir(input_dir)
    files = _fmr_files(source_dir)
    if not files:
        raise FileNotFoundError(f"No standard FMR workbooks found in {source_dir}")

    results = [_validate_file(path) for path in files]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_validation_report(results, source_dir), encoding="utf-8")
    return results


def render_validation_report(results: list[BronzeFMRFileValidation], source_dir: Path) -> str:
    """Render Bronze validation results as Markdown."""
    schema_count = len({result.schema_signature for result in results})
    ready = all(result.is_valid for result in results)
    lines = [
        "# HUD FMR Bronze Validation Summary",
        "",
        f"- Generated at: `{datetime.now(UTC).isoformat()}`",
        f"- Source directory: `{source_dir}`",
        f"- Files validated: {len(results)}",
        f"- Schema variants detected: {schema_count}",
        f"- BRONZE_FMR_READY = {'TRUE' if ready else 'FALSE'}",
        "",
        "| File | FY | Rows | Columns | Missing concepts | Bad FIPS | Bad HUD code | Duplicate FIPS | Null rents | Valid |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            f"`{Path(result.file_path).name}` | "
            f"{result.fiscal_year} | "
            f"{result.row_count:,} | "
            f"{result.column_count:,} | "
            f"{', '.join(result.missing_required_concepts) or 'None'} | "
            f"{result.malformed_fips_count:,} | "
            f"{result.malformed_hud_area_code_count:,} | "
            f"{result.duplicate_fips10_count:,} | "
            f"{result.null_rent_count:,} | "
            f"{'TRUE' if result.is_valid else 'FALSE'} |"
        )
    lines.extend(
        [
            "",
            "## Schema Drift",
            "",
            "Schema drift is expected across years and is handled by the Silver transformer through concept-level mappings.",
        ]
    )
    for signature in sorted({result.schema_signature for result in results}):
        years = [str(result.fiscal_year) for result in results if result.schema_signature == signature]
        lines.append(f"- FY {', '.join(years)}: `{signature}`")
    return "\n".join(lines) + "\n"


def _validate_file(path: Path) -> BronzeFMRFileValidation:
    fiscal_year = _extract_fiscal_year(path)
    with iter_repaired_excel_path(path) as readable_path:
        with pd.ExcelFile(readable_path) as excel:
            sheet_name = _data_sheet(excel.sheet_names)
            df = pd.read_excel(excel, sheet_name=sheet_name, dtype=object).dropna(how="all")

    df = _standardize_columns(df)
    missing = _missing_required_concepts(df)
    fips_column = _first_present(df, ["fips", "fips2010"])
    hud_area_code_column = _first_present(df, ["hud_area_code", "metro_code"])
    fips10 = df[fips_column].map(_format_fips10) if fips_column else pd.Series(dtype="string")
    malformed_fips = int((~fips10.fillna("").str.match(r"^\d{10}$")).sum()) if fips_column else len(df)
    malformed_hud = int(
        (~df[hud_area_code_column].fillna("").astype(str).str.strip().str.match(r"^[A-Z0-9]+[A-Z0-9_ -]*$")).sum()
    ) if hud_area_code_column else len(df)
    duplicate_fips = int(fips10.duplicated().sum()) if fips_column else 0
    null_rents = int(df[[col for col in RENT_COLUMNS if col in df.columns]].isna().sum().sum())
    signature = ", ".join(df.columns.astype(str).tolist())
    return BronzeFMRFileValidation(
        file_path=str(path),
        fiscal_year=fiscal_year,
        sheet_name=sheet_name,
        row_count=len(df),
        column_count=len(df.columns),
        missing_required_concepts=missing,
        malformed_fips_count=malformed_fips,
        malformed_hud_area_code_count=malformed_hud,
        duplicate_fips10_count=duplicate_fips,
        null_rent_count=null_rents,
        schema_signature=signature,
    )


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
    df.columns = [_normalize_column(column) for column in df.columns]
    return df


def _normalize_column(column: object) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", str(column)).strip("_").lower()


def _missing_required_concepts(df: pd.DataFrame) -> list[str]:
    columns = set(df.columns)
    missing: list[str] = []
    for concept, variants in REQUIRED_CONCEPTS.items():
        if not columns.intersection(variants):
            missing.append(concept)
    for rent_column in RENT_COLUMNS:
        if rent_column not in columns:
            missing.append(rent_column)
    return missing


def _first_present(df: pd.DataFrame, columns: list[str]) -> str | None:
    return next((column for column in columns if column in df.columns), None)


def _format_fips10(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if not text.isdigit():
        return text
    return text.zfill(10)


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
    """Run Bronze FMR validation from the command line."""
    parser = argparse.ArgumentParser(description="Validate Bronze HUD FMR workbooks")
    parser.add_argument("--input-dir", default=str(REQUESTED_INPUT_DIR))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args()
    results = validate_fmr_bronze(Path(args.input_dir), Path(args.report_path))
    invalid = [result for result in results if not result.is_valid]
    print(f"Validated {len(results)} FMR workbook(s); invalid={len(invalid)}")
    if invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
