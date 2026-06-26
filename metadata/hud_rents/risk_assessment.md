# HUD Rent Risk Assessment

## Schema Inconsistencies

- FMR changes key names from `fips2010` to `fips`.
- FMR changes HUD area fields from `metro_code` / `areaname` to `hud_area_code` / `hud_area_name`.
- SAFMR FY2020 uses `zcta`, `CBSASub20`, and `Areaname20` instead of the more common ZIP/HUD labels.
- SAFMR FY2025-FY2026 use `HUD Fair Market Rent Area Name` instead of `HUD Metro Fair Market Rent Area Name`.
- ERAP FY2022 uses `CBSASub22`; FY2023-FY2024 use `CBSASub23`.
- FMR optional change metrics appear only in FY2018-FY2020.

## Missing Years

- No SAFMR file is present for FY2018.
- ERAP is present only for FY2022-FY2024.
- Downstream validation must distinguish "not applicable / not present" from failed ingestion.

## Geographic Mapping Risks

- FMR rows are not purely county-level; roughly 1,600 rows per year have a 10-digit FIPS suffix other than `99999`.
- County-level joins from FMR should use `county_fips = left(fips10, 5)` but this may duplicate multiple FMR rows per county.
- SAFMR and ERAP are ZIP-level; direct county assignment requires an external ZIP-to-county crosswalk.
- ZIPs can span multiple counties, so county relationships need allocation methodology or many-to-many modeling.
- HUD area codes are not identical to existing `MetroArea.cbsa_code`; parsing and validation are required.

## ZIP-to-County Challenges

- ZIP Codes are postal constructs and do not perfectly align to counties.
- ZCTA and ZIP definitions differ.
- FY2020 SAFMR explicitly names `zcta`, while other years say `ZIP Code`.
- A chosen crosswalk should include effective year, allocation percentage if available, and primary county flag if used.

## Metro-to-County Challenges

- `METRO33860M33860` style HUD codes can expose a CBSA-like value, but not every HUD area is a simple CBSA.
- `NCNTY01005N01005` represents non-metropolitan county-style HUD areas.
- HUD Metro FMR Areas may not equal CBSA boundaries exactly.

## ERAP-Specific Complications

- ERAP has fewer columns than SAFMR and no 90/110 percent payment standards.
- ERAP covers only FY2022-FY2024 in Bronze.
- ERAP HUD area cardinality is much larger than SAFMR for overlapping years.
- ERAP should not be merged into SAFMR without explicit business approval.

