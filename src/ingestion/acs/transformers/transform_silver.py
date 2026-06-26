"""Transform Bronze ACS JSON into normalized Silver parquet tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.ingestion.acs.registry import enabled_tables, load_registry, years_for_table


BRONZE_ROOT = Path("data/bronze/acs")
SILVER_ROOT = Path("data/silver/acs")


def transform_silver(
    registry_path: Path = Path("metadata/acs/table_registry.yaml"),
    bronze_root: Path = BRONZE_ROOT,
    silver_root: Path = SILVER_ROOT,
) -> dict[str, pd.DataFrame]:
    """Transform all registry-enabled ACS tables to Silver parquet."""
    registry = load_registry(registry_path)
    outputs: dict[str, pd.DataFrame] = {}
    for table in enabled_tables(registry):
        table_config = registry["tables"][table]
        variables = table_config.get("variables", {})
        if not variables:
            raise ValueError(f"Enabled ACS table {table} has no configured variables")
        frames: list[pd.DataFrame] = []
        for year in years_for_table(registry, table):
            table_dir = bronze_root / str(year) / table.lower()
            if not table_dir.exists():
                raise FileNotFoundError(f"Bronze ACS table directory not found: {table_dir}")
            for path in sorted(table_dir.glob("*.json")):
                frames.append(_transform_file(path, year, variables))
        combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        _validate_table(combined, list(variables.keys()))
        output_path = Path(table_config.get("silver_output", silver_root / f"{table.lower()}.parquet"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_parquet(output_path, index=False)
        print(f"Saved {table} Silver rows={len(combined)} to {output_path}")
        outputs[table] = combined
    return outputs


def _transform_file(path: Path, year: int, variables: dict[str, str]) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))

    header, rows = _split_payload(payload, path)

    df = pd.DataFrame(rows, columns=header)

    out = pd.DataFrame()

    out["tract_fips"] = (
        df["state"].astype(str).str.zfill(2)
        + df["county"].astype(str).str.zfill(3)
        + df["tract"].astype(str).str.zfill(6)
    )

    out["state_fips"] = df["state"].astype(str).str.zfill(2)

    out["county_fips"] = out["tract_fips"].str[:5]

    out["year"] = pd.Series(year, index=df.index, dtype="Int64")

    ACS_SENTINEL_VALUES = {
        -666666666,  # estimate unavailable
        -888888888,  # suppressed
        -999999999,  # missing
    }

    for output_column, variable in variables.items():

        values = pd.to_numeric(
            df[variable],
            errors="coerce",
        )

        values = values.mask(values.isin(ACS_SENTINEL_VALUES))

        # If values contain decimals, keep Float64
        if (values.dropna() % 1 == 0).all():
            out[output_column] = values.astype("Int64")
        else:
            out[output_column] = values.astype("Float64")

    return out


def _split_payload(payload: Any, path: Path) -> tuple[list[str], list[list[Any]]]:
    if not isinstance(payload, list) or len(payload) < 2:
        raise RuntimeError(f"Invalid ACS Bronze payload: {path}")
    return [str(column) for column in payload[0]], payload[1:]


def _validate_table(df: pd.DataFrame, value_columns: list[str]) -> None:
    required = [
        "tract_fips",
        "state_fips",
        "county_fips",
        "year",
        *value_columns,
    ]

    missing = [column for column in required if column not in df.columns]

    if missing:
        raise RuntimeError(
            f"Missing Silver ACS columns: {missing}"
        )

    if not df["tract_fips"].astype(str).str.match(r"^\d{11}$").all():
        raise RuntimeError(
            "tract_fips must be exactly 11 digits"
        )

    if df.duplicated(
        subset=["tract_fips", "year"]
    ).any():
        raise RuntimeError(
            "Silver ACS uniqueness failed for tract_fips + year"
        )

    for column in value_columns:
        negatives = df[column].dropna() < 0

        if negatives.any():
            raise RuntimeError(
                f"Negative ACS values detected in {column}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform ACS Bronze JSON to Silver parquet")
    parser.add_argument("--registry", default="metadata/acs/table_registry.yaml")
    parser.add_argument("--bronze-root", default=str(BRONZE_ROOT))
    parser.add_argument("--silver-root", default=str(SILVER_ROOT))
    args = parser.parse_args()
    transform_silver(Path(args.registry), Path(args.bronze_root), Path(args.silver_root))


if __name__ == "__main__":
    main()
