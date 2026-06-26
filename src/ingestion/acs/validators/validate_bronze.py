"""Validate Bronze ACS JSON files."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from src.ingestion.acs.registry import enabled_states, enabled_tables, load_registry, years_for_table


BRONZE_ROOT = Path("data/bronze/acs")
REPORT_PATH = Path("metadata/acs/bronze_validation_report.md")


@dataclass(frozen=True)
class BronzeValidationResult:
    year: int
    table: str
    state: str
    path: str
    row_count: int
    missing_columns: list[str]
    malformed_tract_fips: int

    @property
    def is_valid(self) -> bool:
        return not self.missing_columns and self.malformed_tract_fips == 0 and self.row_count > 0


def validate_bronze(
    registry_path: Path = Path("metadata/acs/table_registry.yaml"),
    bronze_root: Path = BRONZE_ROOT,
    report_path: Path = REPORT_PATH,
) -> list[BronzeValidationResult]:
    registry = load_registry(registry_path)
    results: list[BronzeValidationResult] = []
    for table in enabled_tables(registry):
        variables = set(registry["tables"][table].get("variables", {}).values())
        for year in years_for_table(registry, table):
            required = {"NAME", "state", "county", "tract", *variables}
            for state in enabled_states(registry):
                path = bronze_root / str(year) / table.lower() / f"{state}.json"
                if not path.exists():
                    results.append(BronzeValidationResult(year, table, state, str(path), 0, sorted(required), 0))
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
                header, rows = _split_payload(payload, path)
                missing = sorted(required.difference(set(header)))
                malformed = _malformed_tract_count(header, rows) if not missing else 0
                results.append(BronzeValidationResult(year, table, state, str(path), len(rows), missing, malformed))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(results), encoding="utf-8")
    return results


def render_report(results: list[BronzeValidationResult]) -> str:
    ready = all(result.is_valid for result in results)
    lines = [
        "# ACS Bronze Validation Report",
        "",
        f"- Generated at: `{datetime.now(UTC).isoformat()}`",
        f"- Files checked: {len(results)}",
        f"- ACS_BRONZE_READY = {'TRUE' if ready else 'FALSE'}",
        "",
        "| Year | Table | State | Rows | Missing columns | Bad tract FIPS | Valid |",
        "| ---: | --- | --- | ---: | --- | ---: | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result.year} | {result.table} | {result.state} | {result.row_count:,} | "
            f"{', '.join(result.missing_columns) or 'None'} | {result.malformed_tract_fips:,} | "
            f"{'TRUE' if result.is_valid else 'FALSE'} |"
        )
    return "\n".join(lines) + "\n"


def _split_payload(payload: Any, path: Path) -> tuple[list[str], list[list[Any]]]:
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[0], list):
        raise RuntimeError(f"Invalid ACS Bronze payload: {path}")
    return [str(column) for column in payload[0]], payload[1:]


def _malformed_tract_count(header: list[str], rows: list[list[Any]]) -> int:
    state_idx = header.index("state")
    county_idx = header.index("county")
    tract_idx = header.index("tract")
    count = 0
    for row in rows:
        tract_fips = f"{str(row[state_idx]).zfill(2)}{str(row[county_idx]).zfill(3)}{str(row[tract_idx]).zfill(6)}"
        if len(tract_fips) != 11 or not tract_fips.isdigit():
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Bronze ACS JSON files")
    parser.add_argument("--registry", default="metadata/acs/table_registry.yaml")
    parser.add_argument("--bronze-root", default=str(BRONZE_ROOT))
    parser.add_argument("--report-path", default=str(REPORT_PATH))
    args = parser.parse_args()
    results = validate_bronze(Path(args.registry), Path(args.bronze_root), Path(args.report_path))
    invalid = [result for result in results if not result.is_valid]
    print(f"Validated {len(results)} ACS Bronze file(s); invalid={len(invalid)}")
    if invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
