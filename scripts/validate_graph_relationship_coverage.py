from __future__ import annotations

from pathlib import Path

import pandas as pd

TRACT_REF_PATH = Path("data/silver/geography/tract_reference.parquet")
HPI_PATH = Path("data/gold/fhfa/tract_hpi_enriched.parquet")
CONFORMING_PATH = Path("data/silver/fhfa/conforming_limits.parquet")
STATES_PATH = Path("data/gold/geography/states.parquet")
METRO_PATH = Path("data/gold/geography/metro_areas.parquet")
REPORT_PATH = Path("metadata/validation/graph_relationship_coverage.md")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_cbsa(value) -> str | None:
    if pd.isna(value):
        return None
    try:
        return str(int(value))
    except Exception:
        return str(value).strip() if str(value).strip() else None


def normalize_state_fips(value) -> str:
    if pd.isna(value):
        return ""
    try:
        return str(int(value)).zfill(2)
    except Exception:
        return str(value).strip().zfill(2)


def normalize_county_fips(value) -> str:
    if pd.isna(value):
        return ""
    try:
        return str(int(value)).zfill(5)
    except Exception:
        return str(value).strip().zfill(5)


def main() -> None:
    df_tract = pd.read_parquet(TRACT_REF_PATH)
    df_hpi = pd.read_parquet(HPI_PATH)
    df_conf = pd.read_parquet(CONFORMING_PATH)
    df_states = pd.read_parquet(STATES_PATH)
    df_metro = pd.read_parquet(METRO_PATH)

    # CensusTract -> County
    tract_group = df_tract.groupby("tract_fips")
    tract_counties = tract_group["county_fips"].nunique(dropna=False)
    tract_state = tract_group["state_fips"].nunique(dropna=False)
    tract_exact_one_county = int((tract_counties == 1).sum())
    tract_exact_one_state = int((tract_state == 1).sum())
    tract_total = int(len(tract_counties))
    tract_orphans = int((tract_counties == 0).sum())
    tract_multi_county = int((tract_counties > 1).sum())
    tract_multi_state = int((tract_state > 1).sum())

    # County -> State from all available county sources
    county_union = pd.concat([
        df_tract[["county_fips", "state_fips"]],
        df_conf[["county_fips", "state_fips"]],
    ], ignore_index=True)
    county_union["state_fips"] = county_union["state_fips"].apply(normalize_state_fips)
    county_union["county_fips"] = county_union["county_fips"].apply(normalize_county_fips)
    county_union = county_union.drop_duplicates().dropna(subset=["county_fips"])
    county_group = county_union.groupby("county_fips")
    county_states = county_group["state_fips"].nunique(dropna=False)
    county_exact_one_state = int((county_states == 1).sum())
    county_multi_state = int((county_states > 1).sum())
    county_total = int(len(county_states))

    # HPISnapshot -> CensusTract
    hpi_total = int(df_hpi.shape[0])
    valid_hpi = int(df_hpi["tract_fips"].isin(df_tract["tract_fips"]).sum())
    orphan_hpi = int(hpi_total - valid_hpi)
    hpi_snapshot_dups = int(df_hpi.duplicated(subset=["tract_fips", "year"], keep=False).sum())

    # ConformingLimitSnapshot -> County
    conf_total = int(df_conf.shape[0])
    valid_county_fips = set(county_union["county_fips"].dropna().astype(str))
    conf_valid_county = int(df_conf["county_fips"].astype(str).isin(valid_county_fips).sum())
    conf_orphan_county = int(conf_total - conf_valid_county)
    conf_county_group = df_conf.groupby("county_fips")
    conf_county_state = conf_county_group["state_fips"].nunique(dropna=False)
    conf_county_exact_one_state = int((conf_county_state == 1).sum())
    conf_county_multi_state = int((conf_county_state > 1).sum())
    conf_snapshot_dups = int(df_conf.duplicated(subset=["county_fips", "year"], keep=False).sum())

    # County CBSA -> MetroArea
    df_conf["cbsa_code"] = df_conf["cbsa_number"].apply(normalize_cbsa)
    cbsa_values = df_conf["cbsa_code"].dropna().unique().tolist()
    metro_values = df_metro["cbsa_code"].dropna().astype(str).unique().tolist()
    cbsa_missing = [v for v in cbsa_values if str(v) not in metro_values]
    cbsa_orphan_count = int(df_conf[~df_conf["cbsa_code"].isna() & ~df_conf["cbsa_code"].astype(str).isin(metro_values)].shape[0])
    cbsa_total = int(len(cbsa_values))

    # Duplicate business keys
    tract_dups = int(df_tract.duplicated(subset=["tract_fips"], keep=False).sum())
    state_dups = int(df_states.duplicated(subset=["state_fips"], keep=False).sum())
    metro_dups = int(df_metro.duplicated(subset=["cbsa_code"], keep=False).sum())
    hpi_snapshot_dups = int(df_hpi.duplicated(subset=["tract_fips", "year"], keep=False).sum())
    conf_snapshot_dups = int(df_conf.duplicated(subset=["county_fips", "year"], keep=False).sum())

    # Relationship coverage percentages
    tract_to_county_pct = tract_exact_one_county / tract_total * 100 if tract_total else 0.0
    county_to_state_pct = county_exact_one_state / county_total * 100 if county_total else 0.0
    hpi_to_tract_pct = valid_hpi / hpi_total * 100 if hpi_total else 0.0
    conf_to_county_pct = conf_valid_county / conf_total * 100 if conf_total else 0.0
    cbsa_to_metro_pct = ((cbsa_total - len(cbsa_missing)) / cbsa_total * 100) if cbsa_total else 100.0

    # report
    report_lines = [
        "# Graph Relationship Coverage Validation",
        "",
        "This report validates the current FHFA relationship coverage against the stable geography and snapshot datasets.",
        "",
        "## Relationship coverage summary",
        "",
        "### 1. Every CensusTract maps to exactly one County",
        f"- Unique CensusTracts: {tract_total}",
        f"- Exactly one county mapping: {tract_exact_one_county}",
        f"- Multiple county mappings: {tract_multi_county}",
        f"- Orphan tracts (zero county mapping): {tract_orphans}",
        f"- Coverage: {tract_to_county_pct:.2f}%",
        "",
        "### 2. Every County maps to exactly one State",
        f"- Unique Counties in tract reference: {county_total}",
        f"- Exactly one state mapping: {county_exact_one_state}",
        f"- Multiple state mappings: {county_multi_state}",
        f"- Coverage: {county_to_state_pct:.2f}%",
        "",
        "### 3. Every HPISnapshot maps to exactly one CensusTract",
        f"- HPISnapshot rows: {hpi_total}",
        f"- Valid tract references: {valid_hpi}",
        f"- Orphan HPISnapshots: {orphan_hpi}",
        f"- Coverage: {hpi_to_tract_pct:.2f}%",
        "",
        "### 4. Every ConformingLimitSnapshot maps to exactly one County",
        f"- ConformingLimitSnapshot rows: {conf_total}",
        f"- Valid county references (derived county domain): {conf_valid_county}",
        f"- Orphan ConformingLimitSnapshots: {conf_orphan_county}",
        f"- Coverage: {conf_to_county_pct:.2f}%",
        "",
        "### 5. Every County CBSA code maps to a MetroArea",
        f"- Unique CBSA codes in conforming limits: {cbsa_total}",
        f"- Missing CBSA mappings: {len(cbsa_missing)}",
        f"- Rows with orphan CBSA code: {cbsa_orphan_count}",
        f"- Coverage: {cbsa_to_metro_pct:.2f}%",
        "",
        "## Orphan records and duplicates",
        "",
        f"- Tract Reference duplicate tract_fips rows: {tract_dups}",
        f"- State duplicate state_fips rows: {state_dups}",
        f"- MetroArea duplicate cbsa_code rows: {metro_dups}",
        f"- HPISnapshot duplicate business keys (tract_fips+year): {hpi_snapshot_dups}",
        f"- ConformingLimitSnapshot duplicate business keys (county_fips+year): {conf_snapshot_dups}",
        "",
        "## Detected orphan examples",
        "",
    ]

    orphan_tracts = tract_counties[tract_counties > 1].index.tolist()[:20]
    if orphan_tracts:
        report_lines.append("- Example tracts with multiple county mappings:")
        report_lines.extend([f"  - {t}" for t in orphan_tracts])
    else:
        report_lines.append("- No tracts with multiple county mappings detected.")

    report_lines.append("")
    if orphan_hpi > 0:
        orphan_hpi_ids = df_hpi.loc[~df_hpi["tract_fips"].isin(df_tract["tract_fips"]), "tract_fips"].dropna().unique()[:20].tolist()
        report_lines.append(f"- Example orphan HPISnapshot tract_fips values: {orphan_hpi_ids}")
    else:
        report_lines.append("- No orphan HPISnapshots detected.")

    report_lines.append("")
    if conf_orphan_county > 0:
        orphan_conf_ids = df_conf.loc[~df_conf["county_fips"].isin(df_tract["county_fips"]), "county_fips"].dropna().unique()[:20].tolist()
        report_lines.append(f"- Example orphan ConformingLimitSnapshot county_fips values: {orphan_conf_ids}")
    else:
        report_lines.append("- No orphan ConformingLimitSnapshots detected.")

    report_lines.append("")
    if cbsa_missing:
        report_lines.append(f"- Example CBSA codes missing MetroArea mapping: {cbsa_missing[:20]}")
    else:
        report_lines.append("- No orphan CBSA codes detected.")

    report_lines.extend([
        "",
        "## Graph readiness assessment",
        "",
    ])

    ready = True
    issues = []
    if tract_multi_county > 0 or tract_orphans > 0:
        ready = False
        issues.append("CensusTract -> County relationship is not fully one-to-one.")
    if county_multi_state > 0:
        ready = False
        issues.append("County -> State relationship has inconsistent state mappings.")
    if orphan_hpi > 0:
        ready = False
        issues.append("Some HPISnapshots do not map to a CensusTract.")
    if conf_orphan_county > 0:
        ready = False
        issues.append("Some ConformingLimitSnapshots do not map to a County.")
    if cbsa_orphan_count > 0:
        ready = False
        issues.append("Some County CBSA codes do not map to a MetroArea.")
    if hpi_snapshot_dups > 0:
        ready = False
        issues.append("Duplicate HPISnapshot business keys detected.")
    if conf_snapshot_dups > 0:
        ready = False
        issues.append("Duplicate ConformingLimitSnapshot business keys detected.")

    report_lines.append(f"- Graph readiness status: {'READY' if ready else 'NOT READY'}")
    report_lines.append("")
    if issues:
        report_lines.append("### Issues detected")
        for issue in issues:
            report_lines.append(f"- {issue}")
    else:
        report_lines.append("All relationship coverage checks passed.")

    ensure_dir(REPORT_PATH.parent)
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Validation report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
