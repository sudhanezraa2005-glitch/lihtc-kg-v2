from pathlib import Path
import pandas as pd

paths = {
    "tract_ref": Path("data/silver/geography/tract_reference.parquet"),
    "conforming": Path("data/silver/fhfa/conforming_limits.parquet"),
    "hpi": Path("data/gold/fhfa/tract_hpi_enriched.parquet"),
}

for name, path in paths.items():
    df = pd.read_parquet(path)
    print("==", name, "==")
    print("columns:", df.columns.tolist())
    print("dtypes:", {c: str(dtype) for c, dtype in df.dtypes.items()})
    print("rows:", len(df))
    print("unique_counts:", {c: int(df[c].nunique(dropna=True)) for c in df.columns})
    print()
