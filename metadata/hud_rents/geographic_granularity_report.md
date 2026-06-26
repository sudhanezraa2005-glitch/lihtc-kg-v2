# HUD Rent Geographic Granularity Report

This audit is based only on files present in `data/bronze/fmr`.

## FMR

Primary granularity: 10-digit FIPS row plus HUD area.

Evidence:

- Rows use `fips2010` in FY2018-FY2022 and `fips` in FY2023-FY2026.
- Values are 10-character codes such as `0100199999`.
- The first five characters are a county FIPS candidate.
- The final five characters are often `99999`, but about 1,600 rows per year are not `99999`, meaning the source is not purely county-level.
- HUD area codes are available as `metro_code` or `hud_area_code`, for example `METRO33860M33860` and `NCNTY01005N01005`.

Business key candidates:

- Preferred snapshot key: `fmr_snapshot_id = fiscal_year + ':' + fips10`
- Natural key: `(fiscal_year, fips10)`
- County join key: `county_fips = left(fips10, 5)`
- State join key: `state_fips`
- HUD area join key: `hud_area_code`
- Metro join key candidate: CBSA code parsed from `hud_area_code` when it has a `METRO...` pattern

Relationship possibilities:

- `(:County)-[:HAS_FMR]->(:FMRSnapshot)` using `county_fips`
- `(:State)-[:HAS_FMR]->(:FMRSnapshot)` using `state_fips`
- `(:MetroArea)-[:HAS_FMR]->(:FMRSnapshot)` only when a reliable CBSA code can be parsed and matched
- Future `HUDArea` node can preserve HUD-specific areas that are neither counties nor current MetroArea nodes

## SAFMR

Primary granularity: ZIP Code/ZCTA plus HUD area.

Evidence:

- FY2019 and FY2021-FY2026 use `ZIP Code`.
- FY2020 uses `zcta`.
- Every SAFMR file has a HUD area code equivalent.
- `(fiscal_year, zip_code, hud_area_code)` has zero duplicate rows in audited files.
- ZIP code alone is not unique because ZIPs can appear in multiple HUD areas.

Business key candidates:

- Preferred snapshot key: `safmr_snapshot_id = fiscal_year + ':' + zip_code + ':' + hud_area_code`
- Natural key: `(fiscal_year, zip_code, hud_area_code)`
- ZIP join key: `zip_code`
- HUD area join key: `hud_area_code`
- Metro join key candidate: CBSA code parsed from `hud_area_code`

Relationship possibilities:

- `(:ZIPCode)-[:HAS_SAFMR]->(:SAFMRSnapshot)` if `ZIPCode` nodes are added
- `(:MetroArea)-[:HAS_SAFMR]->(:SAFMRSnapshot)` when `hud_area_code` maps cleanly to CBSA
- `(:County)-[:HAS_SAFMR]->(:SAFMRSnapshot)` only through an external ZIP-to-county crosswalk; avoid direct county assertion from these files alone

## ERAP

Primary granularity: ZIP Code plus HUD area.

Evidence:

- ERAP files contain `ZIP Code` and `CBSASub22` / `CBSASub23`.
- `(fiscal_year, zip_code, hud_area_code)` has zero duplicate rows in audited files.
- ERAP HUD area cardinality is much larger than SAFMR in the same period, indicating a separate emergency rent product rather than a simple SAFMR alias.

Business key candidates:

- Preferred snapshot key: `erap_snapshot_id = fiscal_year + ':' + zip_code + ':' + hud_area_code`
- Natural key: `(fiscal_year, zip_code, hud_area_code)`
- ZIP join key: `zip_code`
- HUD area join key: `hud_area_code`

Relationship possibilities:

- `(:ZIPCode)-[:HAS_ERAP]->(:ERAPSnapshot)` if `ZIPCode` nodes are added
- `(:MetroArea)-[:HAS_ERAP]->(:ERAPSnapshot)` only after HUD area/CBSA parsing is validated
- `(:County)-[:HAS_ERAP]->(:ERAPSnapshot)` only through a ZIP-to-county crosswalk or HUD area mapping table

