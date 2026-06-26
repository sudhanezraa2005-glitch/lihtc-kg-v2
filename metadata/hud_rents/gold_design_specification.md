# HUD Rent Gold Design Specification

No graph loaders or ontology changes are implemented by this document.

## Reference Nodes Needed

Existing graph reference nodes:

- `State`
- `County`
- `MetroArea`
- `CensusTract`

Additional recommended reference node:

- `ZIPCode`, required before SAFMR/ERAP can be connected at their native granularity.

Optional future reference node:

- `HUDArea`, recommended if HUD-specific area codes must be preserved independently from CBSA/MetroArea.

## `FMRSnapshot`

Business key:

- `fmr_snapshot_id`

Properties:

- `fiscal_year`
- `fips10`
- `state_fips`
- `county_fips`
- `county_subdivision_code`
- `hud_area_code`
- `hud_area_name`
- `county_name`
- `county_town_name`
- `state_abbr`
- `is_metro`
- `population`
- `population_source_column`
- `fmr_0br`
- `fmr_1br`
- `fmr_2br`
- `fmr_3br`
- `fmr_4br`
- optional historical fields: `fmr_type`, `acs_2br`, `fmr_pct_chg`, `fmr_dollar_chg`

Relationships:

- `(:County)-[:HAS_FMR]->(:FMRSnapshot)` using `county_fips`
- `(:State)-[:HAS_FMR]->(:FMRSnapshot)` using `state_fips`
- `(:MetroArea)-[:HAS_FMR]->(:FMRSnapshot)` only when `hud_area_code` can be parsed to a matching `cbsa_code`
- Future: `(:HUDArea)-[:HAS_FMR]->(:FMRSnapshot)` using `hud_area_code`

## `SAFMRSnapshot`

Business key:

- `safmr_snapshot_id`

Properties:

- `fiscal_year`
- `zip_code`
- `hud_area_code`
- `hud_area_name`
- `safmr_0br`
- `safmr_1br`
- `safmr_2br`
- `safmr_3br`
- `safmr_4br`
- `safmr_0br_90pct_payment_standard`
- `safmr_1br_90pct_payment_standard`
- `safmr_2br_90pct_payment_standard`
- `safmr_3br_90pct_payment_standard`
- `safmr_4br_90pct_payment_standard`
- `safmr_0br_110pct_payment_standard`
- `safmr_1br_110pct_payment_standard`
- `safmr_2br_110pct_payment_standard`
- `safmr_3br_110pct_payment_standard`
- `safmr_4br_110pct_payment_standard`

Relationships:

- `(:ZIPCode)-[:HAS_SAFMR]->(:SAFMRSnapshot)` using `zip_code`
- `(:MetroArea)-[:HAS_SAFMR]->(:SAFMRSnapshot)` only after validated HUD area to CBSA parsing
- `(:County)-[:HAS_SAFMR]->(:SAFMRSnapshot)` only through an explicit ZIP-to-county allocation/crosswalk
- Future: `(:HUDArea)-[:HAS_SAFMR]->(:SAFMRSnapshot)` using `hud_area_code`

## `ERAPSnapshot`

Business key:

- `erap_snapshot_id`

Properties:

- `fiscal_year`
- `zip_code`
- `hud_area_code`
- `hud_area_name`
- `erap_fmr_0br`
- `erap_fmr_1br`
- `erap_fmr_2br`
- `erap_fmr_3br`
- `erap_fmr_4br`

Relationships:

- `(:ZIPCode)-[:HAS_ERAP]->(:ERAPSnapshot)` using `zip_code`
- `(:MetroArea)-[:HAS_ERAP]->(:ERAPSnapshot)` only after validated HUD area to CBSA parsing
- `(:County)-[:HAS_ERAP]->(:ERAPSnapshot)` only through an explicit ZIP-to-county allocation/crosswalk
- Future: `(:HUDArea)-[:HAS_ERAP]->(:ERAPSnapshot)` using `hud_area_code`

## Constraints and Indexes To Add Later

Recommended uniqueness constraints:

- `FMRSnapshot(fmr_snapshot_id)`
- `SAFMRSnapshot(safmr_snapshot_id)`
- `ERAPSnapshot(erap_snapshot_id)`
- `ZIPCode(zip_code)` if ZIP reference nodes are added
- `HUDArea(hud_area_code)` if HUD area reference nodes are added

Recommended lookup indexes:

- `FMRSnapshot(county_fips)`
- `FMRSnapshot(state_fips)`
- `FMRSnapshot(hud_area_code)`
- `SAFMRSnapshot(zip_code)`
- `SAFMRSnapshot(hud_area_code)`
- `ERAPSnapshot(zip_code)`
- `ERAPSnapshot(hud_area_code)`

