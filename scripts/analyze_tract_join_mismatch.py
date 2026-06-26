from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

HPI_PATH = Path("data/silver/fhfa/tract_hpi.parquet")
REF_PATH = Path("data/silver/geography/tract_reference.parquet")
OUTPUT_PATH = Path("metadata/validation/tract_join_analysis.json")


def normalize_string(values: pd.Series) -> pd.Series:
    return values.fillna("").astype(str).str.strip()


def normalize_pad_hpi(values: pd.Series) -> pd.Series:
    normalized = normalize_string(values)
    return normalized.apply(lambda x: x.zfill(11) if x != "" and x.isdigit() else x)


def normalize_strip_geo(values: pd.Series) -> pd.Series:
    normalized = normalize_string(values)
    return normalized.apply(lambda x: x.lstrip("0") if x != "" else x)


def normalize_as_int(values: pd.Series) -> pd.Series:
    normalized = normalize_string(values)
    def to_int(x: str) -> str:
        try:
            return str(int(x))
        except Exception:
            return ""

    return normalized.apply(to_int)


def sample_values(values: set[str], count: int = 20) -> list[str]:
    sample = sorted(values)[:count]
    return sample


def analyze() -> None:
    df_hpi = pd.read_parquet(HPI_PATH)
    df_ref = pd.read_parquet(REF_PATH)

    hpi_key = "tract"
    ref_key = "tract_fips"

    if hpi_key not in df_hpi.columns:
        raise KeyError(f"Expected HPI key column '{hpi_key}' not found")
    if ref_key not in df_ref.columns:
        raise KeyError(f"Expected geography key column '{ref_key}' not found")

    hpi_raw = df_hpi[hpi_key]
    ref_raw = df_ref[ref_key]

    total_fhfa = int(hpi_raw.nunique(dropna=True))
    total_geography = int(ref_raw.nunique(dropna=True))

    field_analysis: dict[str, Any] = {
        "hpi_dtype": str(hpi_raw.dtype),
        "geo_dtype": str(ref_raw.dtype),
        "hpi_length_distribution": hpi_raw.dropna().astype(str).str.len().value_counts().sort_index().to_dict(),
        "geo_length_distribution": ref_raw.dropna().astype(str).str.len().value_counts().sort_index().to_dict(),
        "hpi_leading_zero_count": int(hpi_raw.dropna().astype(str).str.match(r"^0+").sum()),
        "geo_leading_zero_count": int(ref_raw.dropna().astype(str).str.match(r"^0+").sum()),
    }

    strategies = {
        "Strategy A": {
            "description": "Convert both keys to string without additional normalization",
            "normalize_hpi": normalize_string,
            "normalize_geo": normalize_string,
        },
        "Strategy B": {
            "description": "Left-pad FHFA tract IDs to 11 digits",
            "normalize_hpi": normalize_pad_hpi,
            "normalize_geo": normalize_string,
        },
        "Strategy C": {
            "description": "Remove leading zeros from geography GEOID",
            "normalize_hpi": normalize_string,
            "normalize_geo": normalize_strip_geo,
        },
        "Strategy D": {
            "description": "Compare tract IDs as integers",
            "normalize_hpi": normalize_as_int,
            "normalize_geo": normalize_as_int,
        },
    }

    results: dict[str, Any] = {}
    best_strategy = None
    best_match_rate = -1.0

    for name, config in strategies.items():
        hpi_norm = config["normalize_hpi"](hpi_raw).replace({"": pd.NA})
        geo_norm = config["normalize_geo"](ref_raw).replace({"": pd.NA})

        hpi_set = {x for x in hpi_norm.dropna().astype(str).unique() if x != ""}
        geo_set = {x for x in geo_norm.dropna().astype(str).unique() if x != ""}

        matched = hpi_set & geo_set
        unmatched = hpi_set - geo_set

        match_rate = len(matched) / len(hpi_set) if hpi_set else 0.0

        results[name] = {
            "description": config["description"],
            "fhfa_unique_tracts": int(len(hpi_set)),
            "geography_unique_tracts": int(len(geo_set)),
            "matched_unique_tracts": int(len(matched)),
            "unmatched_unique_tracts": int(len(unmatched)),
            "match_rate": match_rate,
            "sample_matched_tract_ids": sample_values(matched, count=20),
            "sample_unmatched_tract_ids": sample_values(unmatched, count=20),
        }

        if match_rate > best_match_rate:
            best_match_rate = match_rate
            best_strategy = name

    output = {
        "total_fhfa_tracts": total_fhfa,
        "total_geography_tracts": total_geography,
        "field_analysis": field_analysis,
        "strategy_results": results,
        "best_strategy": best_strategy,
        "best_match_rate": best_match_rate,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote analysis to {OUTPUT_PATH}")


if __name__ == "__main__":
    analyze()
