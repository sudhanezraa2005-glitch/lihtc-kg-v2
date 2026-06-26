# HUD FMR Silver Schema Documentation

Output:

- `data/silver/hud/fmr.parquet`

Business key:

- `fmr_snapshot_id = county_fips + "_" + fiscal_year`

Columns:

| Column | Type | Notes |
| --- | --- | --- |
| `fiscal_year` | int | Derived from filename |
| `fmr_snapshot_id` | string | County-year business key |
| `fips10` | string | Selected source 10-digit FIPS row |
| `state_fips` | string | First two digits of `fips10` |
| `county_fips` | string | First five digits of `fips10` |
| `hud_area_code` | string | From `metro_code` or `hud_area_code` |
| `hud_area_name` | string | From `areaname` or `hud_area_name` |
| `county_name` | string | From `countyname` |
| `county_town_name` | string | Nullable |
| `state_abbr` | string | From `state_alpha` or `stusps` |
| `is_metro` | bool | From source `metro` flag |
| `population` | int | From available population column |
| `fmr_0br`-`fmr_4br` | int | Nullable integer rents |
| `source_type` | string | `HUD_FMR` |
| `source_file` | string | Bronze workbook path |

County-year selection rule:

- Standard FMR Bronze contains multiple 10-digit FIPS rows for some counties.
- The production Silver schema is county-year keyed.
- The transformer selects the row whose `fips10` ends with `99999` when present.
- If no `99999` row exists, the transformer selects the first stable sorted FIPS row for that county-year.

