from __future__ import annotations

import json
import itertools
import re
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

INPUT_DIR = Path("data/raw/fhfa/conforming_limits")
OUTPUT_JSON = Path("metadata/profiling/conforming_limits_profile.json")

COUNTY_PATTERNS = [r"county", r"county_name", r"county_fips", r"cnty", r"cty", r"fips"]
STATE_PATTERNS = [r"state", r"state_code", r"state_fips", r"st"]
LOAN_LIMIT_PATTERNS = [r"limit", r"loan_limit", r"conform", r"conforming", r"limit_amount", r"loanamt"]
YEAR_PATTERNS = [r"year", r"yr", r"yyyy", r"period"]


def _matches_any(column_name: str, patterns: List[str]) -> bool:
    return any(re.search(pattern, column_name, re.IGNORECASE) for pattern in patterns)


def _candidate_primary_keys(df: pd.DataFrame) -> List[str]:
    candidates: List[str] = []
    for col in df.columns:
        ser = df[col]
        if ser.notna().all() and ser.is_unique:
            candidates.append(col)
    return candidates


def _identify_county_columns(df: pd.DataFrame) -> List[str]:
    return [col for col in df.columns if _matches_any(col, COUNTY_PATTERNS)]


def _identify_state_columns(df: pd.DataFrame) -> List[str]:
    return [col for col in df.columns if _matches_any(col, STATE_PATTERNS)]


def _identify_loan_limit_columns(df: pd.DataFrame) -> List[str]:
    cols = [col for col in df.columns if _matches_any(col, LOAN_LIMIT_PATTERNS) and pd.api.types.is_numeric_dtype(df[col])]
    if not cols:
        cols = [col for col in df.columns if 'limit' in col.lower() and pd.api.types.is_numeric_dtype(df[col])]
    return cols


def _identify_year_columns(df: pd.DataFrame) -> List[str]:
    year_cols = [col for col in df.columns if _matches_any(col, YEAR_PATTERNS)]
    # also include integer-like columns with 4-digit values
    for col in df.select_dtypes(include=["int", "Int64", "float"]).columns:
        if df[col].dropna().empty:
            continue
        sample = df[col].dropna().astype(int).astype(str)
        if sample.str.match(r"^\d{4}$").all():
            year_cols.append(col)
    return sorted(set(year_cols))


def _find_composite_keys(df: pd.DataFrame, candidate_cols: List[str], max_comb=3) -> List[List[str]]:
    found: List[List[str]] = []
    n = df.shape[0]
    # limit candidate columns to reasonable number
    for r in range(2, min(max_comb, len(candidate_cols)) + 1):
        for combo in itertools.combinations(candidate_cols, r):
            subset = df[list(combo)].dropna()
            if subset.shape[0] != n:
                continue
            if df.duplicated(subset=list(combo)).sum() == 0:
                found.append(list(combo))
    return found


def _read_data(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def profile_file(path: Path) -> Dict[str, Any]:
    df = _read_data(path)
    candidate_pks = _candidate_primary_keys(df)
    county_cols = _identify_county_columns(df)
    state_cols = _identify_state_columns(df)
    year_cols = _identify_year_columns(df)
    loan_limits = _identify_loan_limit_columns(df)

    # for composite key discovery, consider natural candidate columns
    candidate_cols_for_combo = list(dict.fromkeys(candidate_pks + state_cols + county_cols + year_cols))
    composite_keys = _find_composite_keys(df, candidate_cols_for_combo)

    profile: Dict[str, Any] = {
        "file_name": path.name,
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": df.isna().sum().astype(int).to_dict(),
        "candidate_primary_keys": candidate_pks,
        "candidate_composite_keys": composite_keys,
        "county_identifiers": county_cols,
        "state_identifiers": state_cols,
        "loan_limit_columns": loan_limits,
        "year_columns": year_cols,
    }
    return profile


def profile_conforming_limits(input_dir: Path = INPUT_DIR, output_json: Path = OUTPUT_JSON) -> Path:
    input_dir = Path(input_dir)
    files = []
    if input_dir.exists():
        for p in sorted(input_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in {".csv", ".xls", ".xlsx"}:
                files.append(p)

    result: Dict[str, Any] = {"files": {}, "summary": {}}

    total_rows = 0
    total_files = 0
    union_columns = set()

    for file_path in files:
        try:
            prof = profile_file(file_path)
        except Exception as exc:
            prof = {"file_name": file_path.name, "error": str(exc)}
        result["files"][file_path.name] = prof
        if "row_count" in prof:
            total_rows += prof["row_count"]
        total_files += 1
        if "column_names" in prof:
            union_columns.update(prof["column_names"])

    summary = {
        "total_files": total_files,
        "total_rows": int(total_rows),
        "union_column_count": len(union_columns),
        "union_columns": sorted(union_columns),
    }

    result["summary"] = summary

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output_json


def print_summary(profile_path: Path, profile: dict) -> None:
    print("Conforming Limits profiling summary")
    print("-----------------------------------")
    print(f"Profile JSON: {profile_path}")
    print(f"Total files: {profile['summary'].get('total_files', 0)}")
    print(f"Total rows across files: {profile['summary'].get('total_rows', 0)}")
    print(f"Union columns: {profile['summary'].get('union_column_count', 0)} columns")
    print()
    # show per-file highlights with detected schema and keys
    for fname, fprof in profile.get("files", {}).items():
        if 'error' in fprof:
            print(f"- {fname}: ERROR - {fprof['error']}")
            continue
        print(f"File: {fname}")
        print(f"  Rows: {fprof.get('row_count')}  Columns: {fprof.get('column_count')}")
        # detected schema: show name:type for each column
        schema = ", ".join([f"{c}:{fprof['data_types'].get(c, '')}" for c in fprof.get('column_names', [])])
        print(f"  Detected schema: {schema}")
        # candidate business keys
        pks = fprof.get('candidate_primary_keys') or []
        cks = fprof.get('candidate_composite_keys') or []
        print(f"  Candidate business keys (single): {pks}")
        print(f"  Candidate business keys (composite): {cks}")
        # geography
        print(f"  Geography columns - counties: {fprof.get('county_identifiers')}  states: {fprof.get('state_identifiers')}")
        # loan limit measures
        print(f"  Loan limit columns: {fprof.get('loan_limit_columns')}")
        print()


def main() -> None:
    profile_path = profile_conforming_limits()
    profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
    print_summary(profile_path, profile_data)


if __name__ == '__main__':
    main()
