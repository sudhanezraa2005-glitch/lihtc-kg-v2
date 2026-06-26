# Neo4j Mapping Specification for FHFA Ontology

This specification describes the Neo4j mapping for the current FHFA implementation using the following source datasets:

- `data/gold/geography/states.parquet`
- `data/silver/geography/tract_reference.parquet`
- `data/gold/fhfa/tract_hpi_enriched.parquet`
- `data/silver/fhfa/conforming_limits.parquet`
- `data/gold/geography/metro_areas.parquet`

The goal is to map stable geography nodes, temporal snapshot nodes, and supporting MetroArea coverage without generating Cypher or Python code.

---

## 1. Node specification

### State
- Node label: `State`
- Source dataset: `data/gold/geography/states.parquet`
- Business key: `state_fips`
- Properties:
  - `state_fips` (string)
  - `state_abbr` (string)
  - `state_name` (string)
- Unique constraint:
  - `State(state_fips)`
- Indexes:
  - `state_fips`
  - `state_abbr`

### MetroArea
- Node label: `MetroArea`
- Source dataset: `data/gold/geography/metro_areas.parquet`
- Business key: `cbsa_code`
- Properties:
  - `cbsa_code` (string)
- Unique constraint:
  - `MetroArea(cbsa_code)`
- Indexes:
  - `cbsa_code`

### County
- Node label: `County`
- Source dataset: derived from `data/silver/fhfa/conforming_limits.parquet` and `data/silver/geography/tract_reference.parquet`
- Business key: `county_fips`
- Properties:
  - `county_fips` (string)
  - `county_code` (string)
  - `state_fips` (string)
  - `county_name` (string)
  - `cbsa_number` (string) — optional metro identifier
- Unique constraint:
  - `County(county_fips)`
- Indexes:
  - `county_fips`
  - `state_fips`
  - `cbsa_number`

### CensusTract
- Node label: `CensusTract`
- Source dataset: `data/silver/geography/tract_reference.parquet`
- Business key: `tract_fips`
- Properties:
  - `tract_fips` (string)
  - `county_fips` (string)
  - `state_fips` (string)
  - `county_code` (string)
  - `tract_code` (string)
  - `tract_name` (string)
- Unique constraint:
  - `CensusTract(tract_fips)`
- Indexes:
  - `tract_fips`
  - `county_fips`
  - `state_fips`

### HPISnapshot
- Node label: `HPISnapshot`
- Source dataset: `data/gold/fhfa/tract_hpi_enriched.parquet`
- Business key: `snapshot_id`
- Properties:
  - `snapshot_id` (string)
  - `tract_fips` (string)
  - `county_fips` (string)
  - `state_fips` (string)
  - `year` (int)
  - `hpi` (numeric)
  - `annual_change` (numeric)
  - `hpi1990` (numeric)
  - `hpi2000` (numeric)
  - `source_type` (string)
- Unique constraint:
  - `HPISnapshot(snapshot_id)`
- Indexes:
  - `snapshot_id`
  - composite index on `(tract_fips, year)`
  - `year`

### ConformingLimitSnapshot
- Node label: `ConformingLimitSnapshot`
- Source dataset: `data/silver/fhfa/conforming_limits.parquet`
- Business key: `snapshot_id`
- Properties:
  - `snapshot_id` (string)
  - `county_fips` (string)
  - `state_fips` (string)
  - `county_code` (string)
  - `county_name` (string)
  - `state_abbr` (string) — state abbreviation (normalized from source)
  - `cbsa_number` (string)
  - `limit_1_unit` (numeric)
  - `limit_2_unit` (numeric)
  - `limit_3_unit` (numeric)
  - `limit_4_unit` (numeric)
  - `year` (int)
  - `source_type` (string)
- Unique constraint:
  - `ConformingLimitSnapshot(snapshot_id)`
- Indexes:
  - `snapshot_id`
  - composite index on `(county_fips, year)`
  - `year`

---

## 2. Relationship specification

### State CONTAINS County
- Source label: `State`
- Target label: `County`
- Join key: `State.state_fips` = `County.state_fips`
- Cardinality: `State` (1) → `County` (many)

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

### County IN_METRO_AREA MetroArea
- Source label: `County`
- Target label: `MetroArea`
- Join key: `County.cbsa_number` = `MetroArea.cbsa_code`
- Cardinality: `County` (many) → `MetroArea` (1)
- Note: this relationship is only valid for counties with a non-null `cbsa_number` value.

---

## 3. Constraint specification

### Node constraints
- `State`: unique(`state_fips`)
- `MetroArea`: unique(`cbsa_code`)
- `County`: unique(`county_fips`)
- `CensusTract`: unique(`tract_fips`)
- `HPISnapshot`: unique(`snapshot_id`)
- `ConformingLimitSnapshot`: unique(`snapshot_id`)

### Index recommendations
- `State`: index on `state_abbr`
- `MetroArea`: index on `cbsa_code`
- `County`: index on `state_fips`, index on `cbsa_number`
- `CensusTract`: index on `county_fips`, index on `state_fips`
- `HPISnapshot`: composite index on `(tract_fips, year)`, index on `year`
- `ConformingLimitSnapshot`: composite index on `(county_fips, year)`, index on `year`

---

## 4. Recommended load order

1. `State` nodes from `states.parquet`
2. `MetroArea` nodes from `metro_areas.parquet`
3. `County` nodes derived from `conforming_limits.parquet` (and normalized against `tract_reference.parquet` if desired)
4. `CensusTract` nodes from `tract_reference.parquet`
5. `ConformingLimitSnapshot` nodes from `conforming_limits.parquet`
6. `HPISnapshot` nodes from `tract_hpi_enriched.parquet`

### Load order rationale
- `State` first because counties depend on `state_fips`.
- `MetroArea` early because county CBSA relationships can be created as counties are loaded.
- `County` before snapshot nodes so `ConformingLimitSnapshot` and `HPISnapshot` relationships can attach to an existing county or tract.
- `CensusTract` before `HPISnapshot` because snapshots reference tract identifiers.

---

## Notes

- The `CensusTract` node uses `tract_fips` as the canonical tract identifier in this implementation.
- `County` properties should be normalized so `county_fips` and `state_fips` are zero-padded strings.
- `HPISnapshot` and `ConformingLimitSnapshot` both include `snapshot_id` and `source_type` for provenance support, even though lineage nodes are not specified here.
- `County` `IN_METRO_AREA` `MetroArea` mapping is based on `cbsa_number` values that exist in the conforming limits dataset.
