"""Download registry-enabled ACS 5-year tract data to Bronze JSON."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import logging
import os
from pathlib import Path
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from src.ingestion.acs.registry import enabled_states, enabled_tables, load_registry, years_for_table


BRONZE_ROOT = Path("data/bronze/acs")
MANIFEST_PATH = BRONZE_ROOT / "manifest.json"
logger = logging.getLogger(__name__)


def download_acs(
    registry_path: Path = Path("metadata/acs/table_registry.yaml"),
    bronze_root: Path = BRONZE_ROOT,
    retries: int = 3,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Download all registry-enabled ACS files."""
    registry = load_registry(registry_path)
    manifest = _load_manifest()
    records: list[dict[str, Any]] = []
    for table in enabled_tables(registry):
        variables = registry["tables"][table].get("variables", {})
        for year in years_for_table(registry, table):
            if not variables:
                raise ValueError(f"Enabled ACS table {table} has no configured variables")
            for state in enabled_states(registry):
                output_path = bronze_root / str(year) / table.lower() / f"{state}.json"
                if output_path.exists() and not force:
                    record = _manifest_record(year, table, state, output_path, "skipped_existing")
                    records.append(record)
                    manifest.append(record)
                    logger.info("Skipping existing ACS file: %s", output_path)
                    continue
                url = _build_url(registry, year, state, list(variables.values()))
                output_path.parent.mkdir(parents=True, exist_ok=True)
                payload = _request_json(url, retries)
                _validate_payload(payload, table, state)
                output_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
                record = _manifest_record(year, table, state, output_path, "downloaded", row_count=len(payload) - 1)
                records.append(record)
                manifest.append(record)
                logger.info("Downloaded %s rows to %s", len(payload) - 1, output_path)
    _write_manifest(manifest)
    return records


def _build_url(registry: dict[str, Any], year: int, state: str, variables: list[str]) -> str:
    acs = registry["acs"]

    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise ValueError(
            "CENSUS_API_KEY environment variable is not set"
        )

    endpoint = f"{acs['base_url'].rstrip('/')}/{year}/acs/{acs['dataset']}"

    query = {
        "get": ",".join(["NAME", *variables]),
        "for": "tract:*",
        "in": f"state:{state}",
        "key": api_key,
    }

    return f"{endpoint}?{urlencode(query)}"


def _request_json(url: str, retries: int) -> list[list[Any]]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(url, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
            if not isinstance(data, list) or not data:
                raise ValueError("ACS response was not a non-empty JSON array")
            return data
        except Exception as exc:  # noqa: BLE001 - retry boundary
            last_error = exc
            if attempt == retries:
                break
            time.sleep(2**attempt)
    raise RuntimeError(f"ACS download failed after {retries} attempts: {url}") from last_error


def _validate_payload(payload: list[list[Any]], table: str, state: str) -> None:
    header = payload[0]
    required = {"NAME", "state", "county", "tract"}
    missing = required.difference(set(header))
    if missing:
        raise RuntimeError(f"ACS response for {table}/{state} missing columns: {sorted(missing)}")
    if len(payload) <= 1:
        raise RuntimeError(f"ACS response for {table}/{state} contained no data rows")


def _manifest_record(
    year: int,
    table: str,
    state: str,
    path: Path,
    status: str,
    row_count: int | None = None,
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "year": year,
        "table": table,
        "state": state,
        "path": str(path),
        "status": status,
        "row_count": row_count,
    }


def _load_manifest() -> list[dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        return []
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _write_manifest(records: list[dict[str, Any]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="Download ACS 5-year tract data")
    parser.add_argument("--registry", default="metadata/acs/table_registry.yaml")
    parser.add_argument("--bronze-root", default=str(BRONZE_ROOT))
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    download_acs(Path(args.registry), Path(args.bronze_root), args.retries, args.force)


if __name__ == "__main__":
    main()
