# Geography Reference Plan

## Goal
Provide a canonical geography hierarchy for the FHFA knowledge graph, enabling linkage of tract-level data to county and state entities and supporting future ingestion of ACS, HUD, QCT, DDA, AMI, and LIHTC datasets.

## Canonical Geography Hierarchy

### State
- Business key:
  - `state_fips` (primary canonical key)
  - `state_abbr` as a secondary lookup key
- Required attributes:
  - `state_fips` (2-digit zero-padded string)
  - `state_abbr` (2-letter postal code)
  - `state_name` (official state name)
- Source dataset:
  - U.S. Census Bureau state FIPS code list
  - TIGER/Line state reference files
  - authoritative federal geography reference files
- Relationships:
  - `State` CONTAINS `County`

### County
- Business key:
  - `county_fips` (concatenated `state_fips` + `county_code`, string)
- Required attributes:
  - `county_fips` (5-digit zero-padded string)
  - `state_fips` (string)
  - `county_code` (3-digit string)
  - `county_name` (official county name)
- Source dataset:
  - U.S. Census Bureau county FIPS code list
  - TIGER/Line county reference files
  - Census geofile crosswalks for county/state mapping
- Relationships:
  - `County` CONTAINS `CensusTract`
  - `County` belongs to `State`

### CensusTract
- Business key:
  - `tract` (canonical census tract identifier)
  - canonical key may be the full 11-digit tract FIPS when available
- Required attributes:
  - `tract` (string)
  - `state_fips` (string)
  - `county_fips` (string)
  - `county_code` (string)
- Source dataset:
  - U.S. Census Bureau TIGER/Line tract reference files
  - Census tract-to-county crosswalks
  - authoritative tract geography reference files
- Relationships:
  - `CensusTract` belongs to `County`
  - `County` belongs to `State`

## External Dataset Recommendation for tract->county->state Mapping

### Primary recommended external dataset
- U.S. Census Bureau TIGER/Line Census Tract shapefile/reference files
  - contains canonical mappings from tract FIPS to county FIPS and state FIPS
  - provides stable, authoritative geographic hierarchy
  - supports both tract and county identifiers directly

### Supporting datasets for enrichment
- American Community Survey (ACS)
  - use tract/county FIPS codes within ACS tables to add socio-economic variables once the geographic hierarchy is established
- Department of Housing and Urban Development (HUD)
  - HUD program areas also reference tract and county geography; the same FIPS-based mapping can be applied
- Qualified Census Tract (QCT)
  - QCT designations are defined at the tract level and require tract-to-county hierarchy for aggregation and lookup
- Difficult Development Area (DDA)
  - DDA assignments are tract/region-based and need stable tract-county-state mapping for accurate attribution
- Area Median Income (AMI)
  - AMI geographies are often defined at county or metro levels; a stable tract->county->state reference enables joining AMI geography to tract-level records
- Low-Income Housing Tax Credit (LIHTC)
  - LIHTC data frequently references tract and county geographies; canonical FIPS linkage ensures consistent crosswalks

## Plan for Knowledge Graph Implementation

1. Create a stable geography dimension based on the external Census TIGER/Line reference dataset.
2. Load `State`, `County`, and `CensusTract` as stable nodes with only non-temporal attributes.
3. Use the canonical external mapping dataset to populate:
   - `state_fips` and `state_abbr` for `State`
   - `county_fips`, `county_code`, and `county_name` for `County`
   - `tract`, `county_fips`, and `state_fips` for `CensusTract`
4. Ingest FHFA `tract_hpi` data and link to `CensusTract` using tract identifiers.
5. If tract HPI lacks explicit `county_fips`, derive the relationship by joining `tract` to the external tract reference file and then materialize `county_fips`/`state_fips` on the graph link layer.
6. Ingest FHFA `conforming_limits` data as `ConformingLimitSnapshot` nodes linked to `County` via `county_fips`.
7. Support future datasets by using the same canonical geography hierarchy for joins and relationship integrity.

## Notes
- The knowledge graph should treat geography as a separate stable reference layer, not as part of the snapshot datasets.
- The tract-to-county mapping should be managed in a dedicated geography reference ingestion pipeline to ensure consistency across FHFA and future ACS/HUD/QCT/DDA/AMI/LIHTC use cases.
- External reference data should be versioned and recorded as part of lineage metadata to preserve the mapping source.
