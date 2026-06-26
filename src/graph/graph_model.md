# FHFA Graph Model Specification

This document describes the graph model for the FHFA Knowledge Graph based on the available datasets.

## Nodes

### State
- Node label: `State`
- Source dataset: `data/gold/geography/states.parquet`
- Business key: `state_fips`
- Properties:
  - `state_fips`
  - `state_abbr`
  - `state_name`

### MetroArea
- Node label: `MetroArea`
- Source dataset: `data/gold/geography/metro_areas.parquet`
- Business key: `cbsa_code`
- Properties:
  - `cbsa_code`

### County
- Node label: `County`
- Source dataset: derived from `data/silver/fhfa/conforming_limits.parquet` and supplemented by `data/silver/geography/tract_reference.parquet`
- Business key: `county_fips`
- Properties:
  - `county_fips`
  - `county_code`
  - `state_fips`
  - `county_name`
  - `cbsa_number`

### CensusTract
- Node label: `CensusTract`
- Source dataset: `data/silver/geography/tract_reference.parquet`
- Business key: `tract_fips`
- Properties:
  - `tract_fips`
  - `county_fips`
  - `state_fips`
  - `county_code`
  - `tract_code`
  - `tract_name`

### HPISnapshot
- Node label: `HPISnapshot`
- Source dataset: `data/gold/fhfa/tract_hpi_enriched.parquet`
- Business key: `snapshot_id`
- Properties:
  - `snapshot_id`
  - `tract_fips`
  - `county_fips`
  - `state_fips`
  - `year`
  - `hpi`
  - `annual_change`
  - `hpi1990`
  - `hpi2000`
  - `source_type`

### ConformingLimitSnapshot
- Node label: `ConformingLimitSnapshot`
- Source dataset: `data/silver/fhfa/conforming_limits.parquet`
- Business key: `snapshot_id`
- Properties:
  - `snapshot_id`
  - `county_fips`
  - `state_fips`
  - `county_code`
  - `county_name`
  - `State`
  - `cbsa_number`
  - `limit_1_unit`
  - `limit_2_unit`
  - `limit_3_unit`
  - `limit_4_unit`
  - `year`
  - `source_type`

## Relationships

### State CONTAINS County
- Source label: `State`
- Target label: `County`
- Join key: `State.state_fips` = `County.state_fips`
- Cardinality: `State` (1) → `County` (many)

### County IN_METRO_AREA MetroArea
- Source label: `County`
- Target label: `MetroArea`
- Join key: `County.cbsa_number` = `MetroArea.cbsa_code`
- Cardinality: `County` (many) → `MetroArea` (1)
- Note: only for counties with non-null `cbsa_number`

### County CONTAINS CensusTract
- Source label: `County`
- Target label: `CensusTract`
- Join key: `County.county_fips` = `CensusTract.county_fips`
- Cardinality: `County` (1) → `CensusTract` (many)

### CensusTract HAS_HPI HPISnapshot
- Source label: `CensusTract`
- Target label: `HPISnapshot`
- Join key: `CensusTract.tract_fips` = `HPISnapshot.tract_fips`
- Cardinality: `CensusTract` (1) → `HPISnapshot` (many)

### County HAS_CONFORMING_LIMIT ConformingLimitSnapshot
- Source label: `County`
- Target label: `ConformingLimitSnapshot`
- Join key: `County.county_fips` = `ConformingLimitSnapshot.county_fips`
- Cardinality: `County` (1) → `ConformingLimitSnapshot` (many)
