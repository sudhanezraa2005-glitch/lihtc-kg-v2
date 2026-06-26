# FHFA Ontology Coverage Audit

This audit compares the current FHFA implementation against the ontology defined in `metadata/ontology/fhfa_ontology.md`.
It evaluates the available datasets, required entities, attributes, relationships, and metadata needed before Neo4j mapping.

## Current datasets reviewed
- `data/silver/geography/tract_reference.parquet`
- `data/silver/fhfa/conforming_limits.parquet`
- `data/gold/fhfa/tract_hpi_enriched.parquet`

## Dataset schema summary

### tract_reference.parquet
- Columns: `tract_fips`, `state_fips`, `county_code`, `tract_code`, `tract_name`, `county_fips`
- Rows: `85,529`
- Notes: stable `CensusTract` coverage is strong; no explicit `state_abbr` or `state_name`.

### conforming_limits.parquet
- Columns: `state_fips`, `county_code`, `county_name`, `State`, `cbsa_number`, `limit_1_unit`, `limit_2_unit`, `limit_3_unit`, `limit_4_unit`, `year`, `county_fips`
- Rows: `9,703`
- Notes: contains conforming snapshot fields plus geography fields. `state_fips` is stored as `int64`; `State` contains state abbreviations.

### tract_hpi_enriched.parquet
- Columns: `tract_fips`, `county_fips`, `state_fips`, `year`, `hpi`, `annual_change`, `hpi1990`, `hpi2000`
- Rows: `2,179,042`
- Notes: snapshot coverage is complete for HPI and includes geography join keys.

## Entity coverage audit

### State
- Business key in ontology: `state_fips` (preferred), optionally `state_abbr`
- Current attributes available:
  - `state_fips`: yes, in `tract_reference` and `tract_hpi_enriched` as strings, and in `conforming_limits` as integer
  - `state_abbr`: yes, in `conforming_limits.State`
- Missing required attributes:
  - `name`: not present in any reviewed dataset
- Derivable attributes:
  - `state_abbr` can be derived from `conforming_limits.State`
  - `state_fips` can be normalized from `conforming_limits.state_fips`
- Recommended additions:
  - explicit `State` stable entity dataset or canonical lookup
  - `state_name`
  - normalize `state_fips` to string zero-padded format across datasets
- Coverage verdict: partial. state entity is derivable, but required `name` is absent and type normalization is needed.

### County
- Business key in ontology: `county_fips`
- Current attributes available:
  - `county_fips`: yes, in all datasets as string
  - `county_code`: yes, in `tract_reference` and `conforming_limits` (`int64` in conforming)
  - `state_fips`: yes
  - `county_name`: yes, in `conforming_limits`
  - `cbsa_number`: yes, in `conforming_limits`
- Missing required attributes:
  - none required if `county_name` is taken from `conforming_limits`
- Derivable attributes:
  - `county_label` via query-time composition from `county_name` and state abbreviation
- Recommended additions:
  - explicit `County` stable node dataset with canonical `county_name`, `cbsa_number`, and normalized `state_fips`
  - convert `county_code` to string/zero-padded form for ontology consistency
- Coverage verdict: moderate-to-good. county coverage exists but is split across datasets and requires normalization.

### CensusTract
- Business key in ontology: `tract` or canonical full tract identifier
- Current attributes available:
  - `tract_fips`: yes, in `tract_reference` and `tract_hpi_enriched`
  - `county_fips`: yes
  - `state_fips`: yes
  - `tract_name`: yes
- Missing required attributes:
  - none from the current required set; `geotype` is optional and absent but not required
- Derivable attributes:
  - `tract_label` from `tract_fips` + `county_name`
- Recommended additions:
  - rename or alias `tract_fips` to ontology `tract` in Neo4j mapping, or explicitly document the field mapping
  - add optional tract geometry / centroid attributes if spatial queries are planned
- Coverage verdict: good. CensusTract is well represented.

### HPISnapshot
- Business key in ontology: `tract` + `year` (or `tract_year_key`)
- Current attributes available:
  - `tract_fips`: yes
  - `year`: yes
  - `hpi`: yes
  - `annual_change`: yes
  - `hpi1990`: yes
  - `hpi2000`: yes
- Missing required attributes:
  - none for the snapshot payload itself
- Missing/absent ontology metadata attributes:
  - `snapshot_id` or `tract_year_key`: not present
  - lineage/provenance fields: absent
  - `source_type`: absent
  - `data_vintage`: absent
  - `hpi_available`: absent as a stored attribute
- Derivable attributes:
  - `max_limit` not relevant here; `hpi_index_change_from_1990` is derivable at query time
- Recommended additions:
  - add `snapshot_id` or explicit snapshot key if required by Neo4j
  - capture dataset lineage metadata for `HPISnapshot`
  - optionally add `hpi_available` as a boolean or compute on demand
- Coverage verdict: strong for core snapshot data, weak for provenance and metadata.

### ConformingLimitSnapshot
- Business key in ontology: `county_fips` + `year`
- Current attributes available:
  - `county_fips`: yes
  - `year`: yes
  - `limit_1_unit`: yes
  - `limit_2_unit`: yes
  - `limit_3_unit`: yes
  - `limit_4_unit`: yes
- Optional attributes available:
  - `cbsa_number`: yes
- Missing required attributes:
  - none from core conforming snapshot fields
- Missing/absent ontology metadata attributes:
  - `snapshot_id`: absent
  - `source_type`: absent
  - `data_vintage`: absent
  - lineage metadata: absent
- Derivable attributes:
  - `max_limit` can be derived at query time
- Recommended additions:
  - normalize `state_fips` and `county_code` to strings
  - store or generate `snapshot_id`, ingestion metadata, and source provenance
- Coverage verdict: good for core conforming limits, lacking lineage and metadata.

## Relationship validation

### `State` -> `County`
- Feasibility: yes, through `state_fips` on counties
- Current support: implicit only
- Gap: no explicit State node or canonical state name; relationship would be built from `state_fips` values, but the mapping is not fully represented.

### `County` -> `CensusTract`
- Feasibility: yes, via `county_fips` on tract reference
- Current support: good
- Gap: county stable metadata is not centralized in a single canonical dataset, but it is available across current files.

### `CensusTract` -> `HPISnapshot`
- Feasibility: yes, via `tract_fips` and `year`
- Current support: excellent
- Gap: only if `tract_fips` mapping is explicitly aligned with ontology `tract`

### `County` -> `ConformingLimitSnapshot`
- Feasibility: yes, via `county_fips` and `year`
- Current support: excellent

## Metadata and additional attribute checks

### `state_name`
- Status: not available in current datasets
- Recommendation: add via external state lookup or a dedicated state reference dataset

### `state_abbr`
- Status: available now in `conforming_limits.State`
- Recommendation: normalize and propagate to stable State node generation

### `snapshot_id`
- Status: not available
- Recommendation: add ingestion-level snapshot identifiers for both HPISnapshot and ConformingLimitSnapshot datasets

### `source_type`
- Status: not available
- Recommendation: add as provenance metadata in the ingestion pipeline if source classification is required

### `hpi_available`
- Status: not stored
- Recommendation: compute on demand or add as a derived boolean field if downstream consumers require it explicitly

### `data_vintage`
- Status: not stored
- Recommendation: capture dataset versioning or ingestion vintage in lineage metadata

### `lineage metadata`
- Status: absent
- Recommendation: add `DatasetSnapshot` nodes or equivalent ingestion provenance before Neo4j mapping

### `MetroArea (CBSA) node`
- Status: partially available
- Evidence: `conforming_limits.cbsa_number` is present
- Gap: no CBSA name, no CBSA stable entity dataset
- Recommendation: add MetroArea/CBSA reference data if you want to model metropolitan-area relationships explicitly

## Attribute availability categorization

### Available now
- `tract_fips` / `tract` identifier
- `county_fips`
- `state_fips` (as strings in geography and HPI; present as ints in conforming)
- `county_name`
- `tract_name`
- `year`
- HPI measures: `hpi`, `annual_change`, `hpi1990`, `hpi2000`
- Conforming limits: `limit_1_unit`, `limit_2_unit`, `limit_3_unit`, `limit_4_unit`
- `cbsa_number`
- `state_abbr` (from conforming limits)

### Derivable now
- `State` stable nodes from `state_fips` / `state_abbr`
- `County` stable nodes from `county_fips`, `county_name`, `state_fips`
- `CensusTract` stable nodes from `tract_reference`
- `HPISnapshot` and `ConformingLimitSnapshot` nodes from their respective files
- `county_label` and `tract_label` via query-time composition
- `max_limit` from conforming limit columns
- `tract` canonical mapping from `tract_fips`

### Require future datasets or external lookup
- `state_name`
- `DatasetSnapshot` lineage metadata (`dataset_snapshot_id`, `dataset_name`, `source_uri`, `ingestion_timestamp`, `schema_hash`)
- `source_type`
- `data_vintage`
- `MetroArea` names and metadata beyond `cbsa_number`
- optional geography enrichment such as centroids, areas, and spatial indexes

## Required changes before Neo4j

### HIGH PRIORITY
- Add explicit provenance/lineage metadata for snapshot ingestion (DatasetSnapshot nodes)
- Add `snapshot_id` or canonical snapshot business key for both HPISnapshot and ConformingLimitSnapshot
- Normalize `state_fips` and `county_code` to string zero-padded format across all input datasets
- Define or derive an explicit `State` stable node with the required `state_name` attribute
- Confirm and document the field mapping: ontology `tract` <-> dataset `tract_fips`

### MEDIUM PRIORITY
- Create a canonical `County` stable node dataset that centralizes `county_fips`, `county_name`, `state_fips`, and optional `cbsa_number`
- Add `state_abbr` to the stable State entity rather than relying on `conforming_limits` only
- Add `source_type` and `data_vintage` metadata if required by downstream graph semantics
- Add a `MetroArea` or CBSA node dataset if metropolitan relationships are intended to be modeled explicitly

### OPTIONAL
- Add optional tract geography attributes: `geotype`, `centroid_lat`, `centroid_lon`, `area_sq_km`
- Add HPI optional attributes: `hpi_standard_error`, `notes`
- Add ConformingLimitSnapshot optional `notes`
- Add state-level optional geography metadata: `census_region`, `census_division`

## FHFA Ontology Readiness: 75/100

### Rationale
- Strong coverage for snapshot data: HPISnapshot and ConformingLimitSnapshot are present and aligned with the ontology's required measures.
- Good tract-level coverage: `CensusTract` is well represented by `tract_reference.parquet`.
- Partial stability coverage: `County` can be derived, but `State` is not explicitly complete and requires `state_name` plus normalization.
- Major gap: lineage/provenance metadata is missing and should be added before Neo4j mapping.
- Additional improvement: CBSA/MetroArea support is present only as a numeric code and should be enriched if those relationships are needed.
