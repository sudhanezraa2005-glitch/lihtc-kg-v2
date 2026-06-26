#!/usr/bin/env python3
"""Download TIGER/Line 2025 tract shapefiles for all states/territories,
extract selected attributes, and save a concatenated CSV.

Outputs: census_tract_reference_2025.csv in the current folder.

Dependencies: requests, geopandas, pandas
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import pandas as pd
import requests
import geopandas as gpd

BASE_URL = "https://www2.census.gov/geo/tiger/TIGER2025/TRACT"
OUTPUT_CSV = Path("census_tract_reference_2025.csv")

# State FIPS: 01..56 plus territories 60,66,69,72,78
STATE_FIPS: List[str] = [f"{i:02d}" for i in range(1, 57)] + ["60", "66", "69", "72", "78"]

KEEP_COLS = ["GEOID", "STATEFP", "COUNTYFP", "TRACTCE", "NAME"]


def download_and_extract_shapefile(state_fp: str, tmpdir: Path) -> Path | None:
    """Download the ZIP for a state FIPS and extract to tmpdir. Return path to .shp or None."""
    url = f"{BASE_URL}/tl_2025_{state_fp}_tract.zip"
    print(f"[{state_fp}] Downloading {url}")
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            print(f"[{state_fp}] WARNING: HTTP {resp.status_code} for {url}")
            return None
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        z.extractall(tmpdir)
        # locate shapefile
        for shp in Path(tmpdir).rglob("*.shp"):
            return shp
        print(f"[{state_fp}] ERROR: no .shp found in archive")
    except Exception as exc:
        print(f"[{state_fp}] ERROR downloading or extracting: {exc}")
    return None


def process_state(state_fp: str) -> pd.DataFrame | None:
    with TemporaryDirectory() as td:
        tmpdir = Path(td)
        shp = download_and_extract_shapefile(state_fp, tmpdir)
        if shp is None:
            return None
        try:
            print(f"[{state_fp}] Reading shapefile {shp}")
            gdf = gpd.read_file(shp)
        except Exception as exc:
            print(f"[{state_fp}] ERROR reading shapefile: {exc}")
            return None

        cols_present = [c for c in KEEP_COLS if c in gdf.columns]
        missing = [c for c in KEEP_COLS if c not in cols_present]
        if missing:
            print(f"[{state_fp}] WARNING: missing columns {missing} — they will be filled with nulls")

        # create DataFrame with all KEEP_COLS in order, filling missing with NA
        df = pd.DataFrame({})
        for c in KEEP_COLS:
            if c in gdf.columns:
                # convert to string where appropriate
                series = gdf[c]
                # if geometry types or others, coerce
                df[c] = series.astype(str) if series.dtype == object else series
            else:
                df[c] = pd.NA

        # ensure GEOID, STATEFP, COUNTYFP, TRACTCE are strings
        for s in ["GEOID", "STATEFP", "COUNTYFP", "TRACTCE"]:
            if s in df.columns:
                df[s] = df[s].astype(str).str.strip()

        # attach a source state_fips column for debugging if STATEFP missing
        if "STATEFP" not in df.columns or df["STATEFP"].isna().all():
            df["STATEFP"] = state_fp

        print(f"[{state_fp}] Processed {len(df)} rows")
        return df


def main() -> None:
    frames: List[pd.DataFrame] = []

    for sf in STATE_FIPS:
        print(f"Processing state FIPS {sf}...")
        df = process_state(sf)
        if df is None:
            print(f"[{sf}] Skipped")
            continue
        frames.append(df)

    if not frames:
        print("No data downloaded. Exiting.")
        return

    combined = pd.concat(frames, ignore_index=True, sort=False)
    # deduplicate by GEOID if needed (keep first occurrence)
    combined.drop_duplicates(subset=["GEOID"], inplace=True)

    print(f"Saving combined CSV to {OUTPUT_CSV} (rows={len(combined)})")
    combined.to_csv(OUTPUT_CSV, index=False)
    print("Done.")


if __name__ == "__main__":
    main()
