# HUD Rent Schema Comparison Report

Generated from the Bronze files in `data/bronze/fmr`.

## Stable Columns By Dataset Type

### FMR

Stable across FY2018-FY2026 after normalization:

- `fiscal_year`
- `state_fips`
- `county_fips`
- `fips10`
- `hud_area_code`
- `hud_area_name`
- `county_name`
- `county_town_name`
- `metro_flag`
- `fmr_0br`
- `fmr_1br`
- `fmr_2br`
- `fmr_3br`
- `fmr_4br`

### SAFMR

Stable across FY2019-FY2026 after normalization:

- `fiscal_year`
- `zip_code`
- `hud_area_code`
- `hud_area_name`
- `safmr_0br`
- `safmr_0br_90pct_payment_standard`
- `safmr_0br_110pct_payment_standard`
- `safmr_1br`
- `safmr_1br_90pct_payment_standard`
- `safmr_1br_110pct_payment_standard`
- `safmr_2br`
- `safmr_2br_90pct_payment_standard`
- `safmr_2br_110pct_payment_standard`
- `safmr_3br`
- `safmr_3br_90pct_payment_standard`
- `safmr_3br_110pct_payment_standard`
- `safmr_4br`
- `safmr_4br_90pct_payment_standard`
- `safmr_4br_110pct_payment_standard`

### ERAP

Stable across FY2022-FY2024 after normalization:

- `fiscal_year`
- `zip_code`
- `hud_area_code`
- `hud_area_name`
- `erap_fmr_0br`
- `erap_fmr_1br`
- `erap_fmr_2br`
- `erap_fmr_3br`
- `erap_fmr_4br`

## Compatibility Matrix

### FMR Source Column Variants

| Concept | FY2018-FY2020 | FY2021 | FY2022 | FY2023 | FY2024 | FY2025-FY2026 |
| --- | --- | --- | --- | --- | --- | --- |
| FIPS row key | `fips2010` | `fips2010` | `fips2010` | `fips` | `fips` | `fips` |
| HUD area code | `metro_code` | `metro_code` | `metro_code` | `hud_area_code` | `hud_area_code` | `hud_area_code` |
| HUD area name | `areaname` | `areaname` | `areaname` | `hud_area_name` | `hud_area_name` | `hud_area_name` |
| State postal | `state_alpha` | `state_alpha` | `state_alpha` | `state_alpha` | `stusps` | `stusps` |
| Population | `pop2010`/`pop2017` | `pop2017` | `pop2017` | `pop2020` | `pop2020` | `pop2022`/`pop2023` |
| Change metrics | `fmr_pct_chg`, `fmr_dollar_chg` | Missing | Missing | Missing | Missing | Missing |
| FMR type | `fmr_type` | Missing | Missing | Missing | Missing | Missing |
| County numeric code | `county` | `county` | Missing | Missing | Missing | Missing |
| County subdivision | `cousub` | `cousub` | Missing | Missing | Missing | Missing |

### SAFMR Source Column Variants

| Concept | FY2019 | FY2020 | FY2021-FY2024 | FY2025-FY2026 |
| --- | --- | --- | --- | --- |
| ZIP key | `ZIP Code` | `zcta` | `ZIP Code` | `ZIP Code` |
| HUD area code | `HUD Area Code` | `CBSASub20` | `HUD Area Code` | `HUD Area Code` |
| HUD area name | `HUD Metro Fair Market Rent Area Name` | `Areaname20` | `HUD Metro Fair Market Rent Area Name` | `HUD Fair Market Rent Area Name` |
| Payment standard naming | newline-heavy labels | `_90pct_pay_std` / `_110pct_pay_std` | newline-heavy labels | newline-heavy labels |
| Rent columns | 0BR-4BR plus 90/110 pct | 0BR-4BR plus 90/110 pct | 0BR-4BR plus 90/110 pct | 0BR-4BR plus 90/110 pct |

### ERAP Source Column Variants

| Concept | FY2022 | FY2023 | FY2024 |
| --- | --- | --- | --- |
| HUD area code | `CBSASub22` | `CBSASub23` | `CBSASub23` |
| HUD area name | `HUD Fair Market Rent Area Name` | `HUD Metro Fair Market Rent Area Name` | `HUD Metro Fair Market Rent Area Name` |
| ZIP key | `ZIP Code` | `ZIP Code` | `ZIP Code` |
| Rent columns | `erap_fmr_br0`-`erap_fmr_br4` | Same | Same |

## Datatype Inconsistencies

- `state` is numeric in some FMR years and string/zero-padded in others; normalize to two-character `state_fips`.
- `metro` is numeric in several FMR years and string in others; normalize to boolean `is_metro`.
- `fips2010` / `fips` must be read as string and zero-padded to 10 characters.
- `ZIP Code` / `zcta` must be read as string and zero-padded to 5 characters.
- HUD area code columns are string-like but have renamed source headers by year.
- Rent values are integer-like in all audited files.

## Missing Years

- FMR: no missing FY2018-FY2026 years.
- SAFMR: FY2018 missing.
- ERAP: only FY2022-FY2024 present.

