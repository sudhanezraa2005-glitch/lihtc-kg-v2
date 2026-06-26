# FHFA Graph Implementation Plan

This implementation plan summarizes the graph infrastructure specifications for the FHFA Knowledge Graph.

## Nodes

- `State`
  - Source: `data/gold/geography/states.parquet`
  - Business key: `state_fips`
  - Core properties: `state_fips`, `state_abbr`, `state_name`

- `MetroArea`
  - Source: `data/gold/geography/metro_areas.parquet`
  - Business key: `cbsa_code`
  - Core properties: `cbsa_code`

- `County`
  - Source: `data/silver/fhfa/conforming_limits.parquet` (+ `tract_reference` for validation)
  - Business key: `county_fips`
  - Core properties: `county_fips`, `county_code`, `state_fips`, `county_name`, `cbsa_number`

- `CensusTract`
  - Source: `data/silver/geography/tract_reference.parquet`
  - Business key: `tract_fips`
  - Core properties: `tract_fips`, `county_fips`, `state_fips`, `county_code`, `tract_code`, `tract_name`

- `HPISnapshot`
  - Source: `data/gold/fhfa/tract_hpi_enriched.parquet`
  - Business key: `snapshot_id`
  - Core properties: `snapshot_id`, `tract_fips`, `county_fips`, `state_fips`, `year`, `hpi`, `annual_change`, `hpi1990`, `hpi2000`, `source_type`

- `ConformingLimitSnapshot`
  - Source: `data/silver/fhfa/conforming_limits.parquet`
  - Business key: `snapshot_id`
  - Core properties: `snapshot_id`, `county_fips`, `state_fips`, `county_code`, `county_name`, `State`, `cbsa_number`, `limit_1_unit`, `limit_2_unit`, `limit_3_unit`, `limit_4_unit`, `year`, `source_type`

## Relationships

- `State` CONTAINS `County`
- `County` BELONGS_TO `MetroArea`
- `County` CONTAINS `CensusTract`
- `CensusTract` HAS_HPI `HPISnapshot`
- `County` HAS_CONFORMING_LIMIT `ConformingLimitSnapshot`

## Constraints

Defined in `src/graph/constraints.cypher`:
- `State(state_fips)`
- `County(county_fips)`
- `MetroArea(cbsa_code)`
- `CensusTract(tract_fips)`
- `HPISnapshot(snapshot_id)`
- `ConformingLimitSnapshot(snapshot_id)`

## Indexes

Defined in `src/graph/indexes.cypher`:
- `State.state_fips`
- `State.state_abbr`
- `County.county_fips`
- `County.state_fips`
- `County.cbsa_number`
- `MetroArea.cbsa_code`
- `CensusTract.tract_fips`
- `CensusTract.county_fips`
- `HPISnapshot.snapshot_id`
- `HPISnapshot.year`
- `HPISnapshot.tract_fips`
- `ConformingLimitSnapshot.snapshot_id`
- `ConformingLimitSnapshot.year`
- `ConformingLimitSnapshot.county_fips`

## Load order

Recommended sequence:
1. `State`
2. `MetroArea`
3. `County`
4. `CensusTract`
5. `HPISnapshot`
6. `ConformingLimitSnapshot`

Relationship sequence:
1. `State` → `County`
2. `County` → `MetroArea`
3. `County` → `CensusTract`
4. `CensusTract` → `HPISnapshot`
5. `County` → `ConformingLimitSnapshot`

## Validation strategy

The graph implementation layer should be validated using the following checks:

- Ontology validation: compare source properties and node labels against `metadata/ontology/fhfa_ontology.md`
- Business key validation: ensure uniqueness of all node business keys
- Duplicate validation: ensure no duplicate snapshot business keys in source datasets
- Orphan validation: ensure all relationships can be resolved from source keys
- Relationship coverage validation: confirm cardinality rules and match percentages

## Notes

- This plan is an infrastructure-only specification.
- No data loading scripts or import code are included.
- The source datasets are the basis for mapping definitions, constraints, and load order.
