# HUD Rent Silver Design Specification

No implementation is included in this document.

## Common Rules

- Preserve raw Bronze files unchanged.
- Read Excel values with explicit string handling for FIPS, ZIP, state, and HUD area codes.
- Normalize column names to snake_case.
- Add `source_file`, `source_sheet`, `dataset_type`, and `ingested_at`.
- Validate row uniqueness before writing Silver.
- Store monetary rent values as nullable integers.

## `silver_hud_fmr`

Normalized columns:

| Column | Type | Rule |
| --- | --- | --- |
| `fiscal_year` | int | Derived from filename |
| `fmr_snapshot_id` | string | `{fiscal_year}:{fips10}` |
| `fips10` | string | From `fips2010` or `fips`, zero-padded to 10 |
| `state_fips` | string | First 2 chars of `fips10` or normalized `state` |
| `county_fips` | string | First 5 chars of `fips10` |
| `county_subdivision_code` | string | Last 5 chars of `fips10` |
| `hud_area_code` | string | From `metro_code` or `hud_area_code` |
| `hud_area_name` | string | From `areaname` or `hud_area_name` |
| `county_name` | string | From `countyname` |
| `county_town_name` | string | From `county_town_name` |
| `state_abbr` | string | From `state_alpha` or `stusps` when present |
| `is_metro` | bool | From `metro` |
| `population` | int | From year-specific population column |
| `population_source_column` | string | Original population column name |
| `fmr_0br`-`fmr_4br` | int | From `fmr_0`-`fmr_4` |
| `fmr_type` | int | Optional; FY2018-FY2020 only |
| `acs_2br` | int | Optional; FY2018-FY2020 only |
| `fmr_pct_chg` | float | Optional; FY2018-FY2020 only |
| `fmr_dollar_chg` | int | Optional; FY2018-FY2020 only |

Business key:

- `fmr_snapshot_id`

Uniqueness constraint:

- `(fiscal_year, fips10)` unique.

Validation rules:

- `fiscal_year` required.
- `fips10` required and exactly 10 digits.
- `county_fips` exactly 5 digits.
- `state_fips` exactly 2 digits.
- `hud_area_code` required.
- Rent columns non-null and non-negative.
- `is_metro` must be true or false.

## `silver_hud_safmr`

Normalized columns:

| Column | Type | Rule |
| --- | --- | --- |
| `fiscal_year` | int | Derived from filename |
| `safmr_snapshot_id` | string | `{fiscal_year}:{zip_code}:{hud_area_code}` |
| `zip_code` | string | From `ZIP Code` or `zcta`, zero-padded to 5 |
| `hud_area_code` | string | From `HUD Area Code` or `CBSASub20` |
| `hud_area_name` | string | From HUD area name variant |
| `safmr_0br`-`safmr_4br` | int | Base SAFMR values |
| `safmr_0br_90pct_payment_standard`-`safmr_4br_90pct_payment_standard` | int | 90 pct values |
| `safmr_0br_110pct_payment_standard`-`safmr_4br_110pct_payment_standard` | int | 110 pct values |

Business key:

- `safmr_snapshot_id`

Uniqueness constraint:

- `(fiscal_year, zip_code, hud_area_code)` unique.

Validation rules:

- `zip_code` required and exactly 5 digits.
- `hud_area_code` required.
- Rent and payment-standard columns non-null and non-negative.
- 90 pct payment standard should be less than or equal to base SAFMR.
- 110 pct payment standard should be greater than or equal to base SAFMR.

## `silver_hud_erap`

Normalized columns:

| Column | Type | Rule |
| --- | --- | --- |
| `fiscal_year` | int | Derived from filename |
| `erap_snapshot_id` | string | `{fiscal_year}:{zip_code}:{hud_area_code}` |
| `zip_code` | string | From `ZIP Code`, zero-padded to 5 |
| `hud_area_code` | string | From `CBSASub22` or `CBSASub23` |
| `hud_area_name` | string | From HUD area name variant |
| `erap_fmr_0br`-`erap_fmr_4br` | int | From `erap_fmr_br0`-`erap_fmr_br4` |

Business key:

- `erap_snapshot_id`

Uniqueness constraint:

- `(fiscal_year, zip_code, hud_area_code)` unique.

Validation rules:

- `zip_code` required and exactly 5 digits.
- `hud_area_code` required.
- ERAP rent columns non-null and non-negative.
- FY coverage must be allowed to be sparse; current files cover FY2022-FY2024 only.

