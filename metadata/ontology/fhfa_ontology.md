# FHFA Ontology Specification

This document specifies the FHFA domain ontology used by the knowledge graph and data warehouse. It defines stable geography entities, temporal snapshot nodes for yearly facts, lineage nodes, keys, attributes, constraints, indexes, and relationships. This is an ontology/specification only — no database or graph code.

## Modeling Principles
- Geography entities are *stable nodes* (no temporal attributes stored on them).
- Yearly facts are modeled as *snapshot nodes* (temporal snapshots with a `year` attribute).
- Lineage provenance is captured via `DatasetSnapshot` nodes; snapshots reference their source dataset.
- Business keys are explicit and immutable for stable nodes; snapshots include a snapshot key and link to the geography entity.

---

## Nodes

### State (stable)
- Business key: `state_fips` OR `state_abbr` (preferred canonical key: `state_fips`)
- Required attributes:
  - `state_fips` (string, 2-digit zero-padded)
  - `state_abbr` (string, 2-letter postal)
  - `name` (string)
- Optional attributes:
  - `census_region` (string)
  - `census_division` (string)
  - `notes` (string)
- Derived attributes:
  - none stored on node; derived aggregations should be computed in snapshot or query layer
- Discarded attributes and reasons:
  - temporal fields (e.g., `population_by_year`) — discarded from geography node to avoid temporal coupling
- Unique constraints:
  - unique(`state_fips`)
  - unique(`state_abbr`)
- Indexes (for lookup):
  - index on `state_fips`
  - index on `state_abbr`

---

### County (stable)
- Business key: `county_fips` (concatenation `state_fips` + `county_code`, string)
- Required attributes:
  - `county_fips` (string, e.g., `06` + `075` = `06075`)
  - `county_code` (string or zero-padded integer)
  - `state_fips` (string)
  - `county_name` (string)
- Optional attributes:
  - `cbsa_number` (string / int) — may be null for rural counties
  - `population` (int) — if available but not stored as temporal here
  - `land_area` (float)
- Derived attributes:
  - `county_label` = `county_name + ', ' + state_abbr` (derivable at query time)
- Discarded attributes and reasons:
  - year-specific loan limits or HPI measures — moved to snapshot nodes
- Unique constraints:
  - unique(`county_fips`)
- Indexes:
  - index on `county_fips`
  - index on `state_fips` for range queries by state

---

### CensusTract (stable)
- Business key: `tract` (string) OR composite (`state_fips`, `county_fips`, `tract`) — canonical: `tract` is a census tract identifier (string)
- Required attributes:
  - `tract` (string; full tract identifier, including state/county prefix when present)
  - `county_fips` (string)
  - `state_fips` (string)
  - `geotype` (optional categorical, e.g., 'tract')
- Optional attributes:
  - `tract_name` (string)
  - `centroid_lat` (float)
  - `centroid_lon` (float)
  - `area_sq_km` (float)
- Derived attributes:
  - `tract_label` = derived from `tract` and `county_name`
- Discarded attributes and reasons:
  - any time-series HPI or loan-limit values — these belong to snapshot nodes
- Unique constraints:
  - unique(`tract`) OR unique composite(`state_fips`,`county_fips`,`tract`) depending on canonicalization
- Indexes:
  - index on `tract`
  - spatial index on centroid if supported in storage layer

---

### HPISnapshot (temporal snapshot node)
- Node purpose: stores HPI measures for a `CensusTract` at a specific `year` (yearly snapshot)
- Business key: composite: `tract` + `year` (or `tract_year_key`)
- Required attributes:
  - `tract` (string) — foreign key to `CensusTract` business key
  - `year` (int)
  - `hpi` (numeric)
  - `annual_change` (numeric)
  - `hpi1990` (numeric)
  - `hpi2000` (numeric)
- Optional attributes:
  - `hpi_standard_error` (numeric)
  - `notes` (string)
- Derived attributes:
  - `hpi_index_change_from_1990` = `hpi` / `hpi1990` - 1 (not stored; computed as needed)
  - rolling averages (computed at query time)
- Discarded attributes and reasons:
  - permanent geography attributes (e.g., centroid) — avoid duplication
- Unique constraints:
  - unique(`tract`, `year`)
- Indexes:
  - index on (`tract`,`year`) (composite) for lookups
  - index on `year` for time-series queries
- Relationships:
  - `CensusTract` HAS_HPI `HPISnapshot` (many snapshots per tract)
  - `HPISnapshot` SOURCED_FROM `DatasetSnapshot` (lineage)

---

### ConformingLimitSnapshot (temporal snapshot node)
- Node purpose: stores the conforming loan limits for a `County` at a specific `year` (yearly snapshot)
- Business key: composite: `county_fips` + `year`
- Required attributes:
  - `county_fips` (string) — foreign key to `County`
  - `year` (int)
  - `limit_1_unit` (numeric)
  - `limit_2_unit` (numeric)
  - `limit_3_unit` (numeric)
  - `limit_4_unit` (numeric)
- Optional attributes:
  - `cbsa_number` (string) — included if present on source
  - `notes` (string)
- Derived attributes:
  - `max_limit` = max(limit_1_unit, limit_2_unit, limit_3_unit, limit_4_unit)
- Discarded attributes and reasons:
  - per-tract HPI values — not relevant to conforming limits snapshot
- Unique constraints:
  - unique(`county_fips`, `year`)
- Indexes:
  - index on (`county_fips`, `year`)
  - index on `year`
- Relationships:
  - `County` HAS_CONFORMING_LIMIT `ConformingLimitSnapshot`
  - `ConformingLimitSnapshot` SOURCED_FROM `DatasetSnapshot`

---

### DatasetSnapshot (lineage / provenance node)
- Node purpose: describes a dataset file or ingestion run used as the source of snapshot data
- Business key: `dataset_snapshot_id` (string/guid) or combination (`dataset_name`, `ingestion_timestamp`)
- Required attributes:
  - `dataset_snapshot_id` (string)
  - `dataset_name` (string)
  - `source_uri` (string/path)
  - `ingestion_timestamp` (timestamp)
  - `schema_hash` (string) — hash of the ingested schema
- Optional attributes:
  - `owner` (string)
  - `notes` (string)
- Derived attributes:
  - none; used for provenance only
- Discarded attributes and reasons:
  - raw binary payloads — store externally if needed
- Unique constraints:
  - unique(`dataset_snapshot_id`)
- Indexes:
  - index on `dataset_name`
  - index on `ingestion_timestamp`

---

## Relationships (explicit)
- `State` CONTAINS `County`  (1 State -> * Counties)
  - cardinality: State (1) —(contains)—> County (many)
  - relationship properties: none required; may include `effective_from` if historical state boundaries are tracked (not in current model)

- `County` CONTAINS `CensusTract`  (1 County -> * Tracts)
  - cardinality: County (1) —(contains)—> CensusTract (many)

- `CensusTract` HAS_HPI `HPISnapshot`  (1 Tract -> * HPISnapshots)
  - cardinality: CensusTract (1) —(has_hpi)—> HPISnapshot (many)
  - HPISnapshot.business_key = (`tract`,`year`)

- `County` HAS_CONFORMING_LIMIT `ConformingLimitSnapshot`  (1 County -> * ConformingLimitSnapshots)
  - cardinality: County (1) —(has_conforming_limit)—> ConformingLimitSnapshot (many)
  - ConformingLimitSnapshot.business_key = (`county_fips`,`year`)

- `HPISnapshot` SOURCED_FROM `DatasetSnapshot`  (many snapshots -> 1 dataset snapshot)
- `ConformingLimitSnapshot` SOURCED_FROM `DatasetSnapshot`

---

## Temporal Modeling Rules (applies to ontology)
1. Geography entities are stable nodes: do not store time-varying facts (HPI, loan limits) on `State`, `County`, or `CensusTract` nodes.
2. Yearly facts are represented as snapshot nodes (`HPISnapshot`, `ConformingLimitSnapshot`) containing a `year` attribute and measures.
3. Do not store temporal versioning attributes (e.g., valid_from/valid_to) on geography nodes in this model; if needed, introduce separate temporal geometry or administrative-boundary snapshot nodes.

---

## Keys, Constraints and Indexing Summary
- Stable nodes:
  - `State`: unique(`state_fips`), index(`state_abbr`)
  - `County`: unique(`county_fips`), index(`state_fips`)
  - `CensusTract`: unique(`tract`) or composite unique(`state_fips`,`county_fips`,`tract`), spatial index optional
- Snapshot nodes:
  - `HPISnapshot`: unique(`tract`,`year`), index(`year`), index(`tract`,`year`)
  - `ConformingLimitSnapshot`: unique(`county_fips`,`year`), index(`year`), index(`county_fips`,`year`)
- Lineage:
  - `DatasetSnapshot`: unique(`dataset_snapshot_id`), index(`dataset_name`), index(`ingestion_timestamp`)

---

## Attribute Categories (explicit lists)

- Required attributes (per node, summarized):
  - `State`: `state_fips`, `state_abbr`, `name`
  - `County`: `county_fips`, `county_code`, `state_fips`, `county_name`
  - `CensusTract`: `tract`, `county_fips`, `state_fips`
  - `HPISnapshot`: `tract`, `year`, `hpi`, `annual_change`, `hpi1990`, `hpi2000`
  - `ConformingLimitSnapshot`: `county_fips`, `year`, `limit_1_unit`, `limit_2_unit`, `limit_3_unit`, `limit_4_unit`
  - `DatasetSnapshot`: `dataset_snapshot_id`, `dataset_name`, `source_uri`, `ingestion_timestamp`, `schema_hash`

- Optional attributes (examples):
  - `State`: `census_region`, `census_division`
  - `County`: `cbsa_number`, `population`, `land_area`
  - `CensusTract`: `centroid_lat`, `centroid_lon`, `area_sq_km`
  - `HPISnapshot`: `hpi_standard_error`, `notes`
  - `ConformingLimitSnapshot`: `cbsa_number`, `notes`

- Derived attributes (should not be stored on stable nodes; compute in snapshots or query layer):
  - `county_label`, `tract_label`, `max_limit`, `hpi_index_change_from_1990`

- Discarded attributes and reasons (examples):
  - raw binary payloads (store externally)
  - repeated geography attributes on snapshot nodes (avoid duplication)
  - historical geometry versions (out of scope; introduce boundary snapshot nodes when needed)

---

## Lineage and Provenance
- Every `HPISnapshot` and `ConformingLimitSnapshot` node MUST link to a `DatasetSnapshot` node via `SOURCED_FROM`.
- `DatasetSnapshot` captures the ingestion timestamp, source file path/URI, and a schema hash to enable reproducibility and audits.

---

## Example: HPISnapshot record (spec)
- Business key: `tract` + `year` (e.g., `1400000US06075010100_2020`)
- Required attrs: `tract`, `year`, `hpi`, `annual_change`, `hpi1990`, `hpi2000`
- Relationship: `HPISnapshot` -> `SOURCED_FROM` -> `DatasetSnapshot`

---

## Notes & Next Actions
- If spatial queries are required, add spatial indexes to `CensusTract` centroids and store geometries externally (e.g., GeoParquet or spatial DB).
- For multi-version geography (changing county boundaries), introduce `CountyBoundarySnapshot` nodes and relate snapshots to geographic versions.
- If you want, I can generate a machine-readable JSON Schema or YAML representation of this ontology for ingestion into tooling.
