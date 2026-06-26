from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def ensure_dir(path: Path) -> None:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)


def read_csv_all_str(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, **kwargs)


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    df.to_parquet(path, index=False)


def profile_df_to_json(df: pd.DataFrame, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    profile = {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": df.isna().sum().astype(int).to_dict(),
        "unique_counts": df.nunique(dropna=False).astype(int).to_dict(),
    }
    output_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
