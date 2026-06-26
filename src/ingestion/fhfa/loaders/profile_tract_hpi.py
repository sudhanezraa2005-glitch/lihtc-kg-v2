from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

INPUT_CSV = Path("data/raw/fhfa/tract_hpi/hpi_at_tract.csv")
OUTPUT_JSON = Path("metadata/profiling/tract_hpi_profile.json")

GEO_PATTERNS = [r"tract", r"county", r"state", r"fips", r"geo", r"region", r"msa"]
TIME_PATTERNS = [r"date", r"year", r"quarter", r"month", r"period", r"time"]
HPI_PATTERNS = [r"hpi", r"index", r"price", r"value", r"median"]


def _matches_any(column_name: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, column_name, re.IGNORECASE) for pattern in patterns)


def _identify_candidate_primary_keys(dataframe: pd.DataFrame) -> list[str]:
    candidates = []
    for column in dataframe.columns:
        series = dataframe[column]
        if series.notna().all() and series.is_unique:
            candidates.append(column)
    return candidates


def _identify_geography_columns(dataframe: pd.DataFrame) -> list[str]:
    return [column for column in dataframe.columns if _matches_any(column, GEO_PATTERNS)]


def _identify_time_columns(dataframe: pd.DataFrame) -> list[str]:
    time_columns = [column for column in dataframe.columns if _matches_any(column, TIME_PATTERNS)]
    datetime_columns = [column for column in dataframe.columns if pd.api.types.is_datetime64_any_dtype(dataframe[column])]
    return sorted(set(time_columns + datetime_columns))


def _identify_hpi_measure_columns(dataframe: pd.DataFrame, exclude_columns: list[str]) -> list[str]:
    measures = [
        column
        for column in dataframe.columns
        if column not in exclude_columns
        and pd.api.types.is_numeric_dtype(dataframe[column])
        and _matches_any(column, HPI_PATTERNS)
    ]

    if not measures:
        measures = [
            column
            for column in dataframe.columns
            if column not in exclude_columns and pd.api.types.is_numeric_dtype(dataframe[column])
        ]
    return measures


def profile_tract_hpi(input_csv: Path = INPUT_CSV, output_json: Path = OUTPUT_JSON) -> Path:
    dataframe = pd.read_csv(input_csv)
    profile = {
        "row_count": int(dataframe.shape[0]),
        "column_count": int(dataframe.shape[1]),
        "column_names": dataframe.columns.tolist(),
        "data_types": {col: str(dtype) for col, dtype in dataframe.dtypes.items()},
        "null_counts": dataframe.isna().sum().astype(int).to_dict(),
        "unique_counts": dataframe.nunique(dropna=False).astype(int).to_dict(),
        "candidate_primary_keys": _identify_candidate_primary_keys(dataframe),
        "geography_columns": _identify_geography_columns(dataframe),
        "time_columns": _identify_time_columns(dataframe),
    }

    exclude_columns = profile["candidate_primary_keys"] + profile["geography_columns"] + profile["time_columns"]
    profile["hpi_measure_columns"] = _identify_hpi_measure_columns(dataframe, exclude_columns)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return output_json


def print_summary(profile_path: Path, profile_data: dict[str, object]) -> None:
    print("Tract HPI profiling summary")
    print("---------------------------")
    print(f"Input CSV: {INPUT_CSV}")
    print(f"Output JSON: {profile_path}")
    print(f"Rows: {profile_data['row_count']}")
    print(f"Columns: {profile_data['column_count']}")
    print(f"Candidate primary keys: {profile_data['candidate_primary_keys']}")
    print(f"Geography columns: {profile_data['geography_columns']}")
    print(f"Time columns: {profile_data['time_columns']}")
    print(f"HPI measure columns: {profile_data['hpi_measure_columns']}")


def main() -> None:
    profile_path = profile_tract_hpi()
    profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
    print_summary(profile_path, profile_data)


if __name__ == "__main__":
    main()
