from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def profile_csv(csv_path: str | Path, output_dir: str | Path = Path("metadata/profiling")) -> Path:
    """Profile a CSV file and save the results as JSON.

    Args:
        csv_path: Path to the input CSV file.
        output_dir: Directory where the JSON profile is saved.

    Returns:
        Path to the saved JSON profile file.
    """
    csv_path = Path(csv_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataframe = pd.read_csv(csv_path)
    profile = {
        "row_count": int(dataframe.shape[0]),
        "column_count": int(dataframe.shape[1]),
        "column_names": dataframe.columns.tolist(),
        "data_types": {col: str(dtype) for col, dtype in dataframe.dtypes.items()},
        "null_counts": dataframe.isna().sum().astype(int).to_dict(),
        "unique_counts": dataframe.nunique(dropna=False).astype(int).to_dict(),
    }

    output_path = output_dir / f"{csv_path.stem}_profile.json"
    output_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return output_path
