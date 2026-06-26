# HUD FMR Gold Schema Documentation

Output:

- `data/gold/hud/fmr_snapshots.parquet`

Graph node:

- `FMRSnapshot`

Business key:

- `snapshot_id`

Columns:

| Column | Type |
| --- | --- |
| `snapshot_id` | string |
| `county_fips` | string |
| `state_fips` | string |
| `year` | int |
| `studio_rent` | int |
| `one_bedroom_rent` | int |
| `two_bedroom_rent` | int |
| `three_bedroom_rent` | int |
| `four_bedroom_rent` | int |
| `hud_area_code` | string |
| `hud_area_name` | string |
| `source_type` | string |

Validation:

- `snapshot_id` unique.
- Required fields non-null.
- `snapshot_id == county_fips + "_" + year`.
- `county_fips` exactly five digits.
- `state_fips` exactly two digits.

