# FHFA Knowledge Graph Design Review

This review evaluates the current FHFA graph design against the existing specifications and available datasets.

## Reviewed artifacts
- `src/graph/graph_model.md`
- `src/graph/constraints.cypher`
- `src/graph/indexes.cypher`
- `src/graph/load_order.md`
- `metadata/ontology/neo4j_mapping_spec.md`
- `metadata/graph/graph_implementation_plan.md`

## Dataset size estimates
- `State` nodes: 56
- `MetroArea` nodes: 994
- `County` nodes: ~3,235 to 3,243
- `CensusTract` nodes: 85,529
- `HPISnapshot` nodes: 2,179,042
- `ConformingLimitSnapshot` nodes: 9,703

## 1. Node design review

### State
- Business key correctness: `state_fips` is correct and canonical.
- Property completeness: core properties are present; missing optional attributes such as `census_region`, `census_division`, and `notes`.
- Duplicate risk: low, with unique constraint defined and no duplicate input rows.
- Future compatibility: good for ACS, FMR, AMI, QCT, DDA, LIHTC because state-level geography is stable.
- Missing attributes: `census_region`, `census_division`, `population`, `area`, and any longitudinal state-level metadata.
- Assessment: strong stable node design.

### MetroArea
- Business key correctness: `cbsa_code` is appropriate for CBSA-based metro coverage.
- Property completeness: minimal placeholder; only `cbsa_code` is present.
- Duplicate risk: low, with unique constraint and no duplicates in the current source.
- Future compatibility: adequate as a backbone node, but metadata is sparse.
- Missing attributes: `cbsa_name`, `metro_type`, `state_fips`, `population`, and any CBSA-level classification.
- Assessment: acceptable as a placeholder, but should be enriched before production use in metro analyses.

### County
- Business key correctness: `county_fips` is the right canonical key.
- Property completeness: necessary keys and `county_name` are available; `cbsa_number` is present for metro linkage.
- Duplicate risk: the node design is safe, though source rows are multi-year; the node should deduplicate on `county_fips`.
- Future compatibility: good for ACS, FMR, QCT, DDA, and LIHTC if county-level attributes are augmented.
- Missing attributes: `state_abbr`, `state_name`, `population`, `area`, `rural_urban_status`, `msa_name`, and `county_label`.
- Assessment: generally sound, but the node is sourced from conforming limits rather than a dedicated county reference dataset.

### CensusTract
- Business key correctness: `tract_fips` is correct for census tract as a stable geography key.
- Property completeness: core geographic linkages exist; `tract_name` and codes are included.
- Duplicate risk: low, with unique constraint and no duplicates discovered.
- Future compatibility: strong for ACS, QCT, DDA, and LIHTC; FMR and AMI typically attach at higher geographic levels, but tract support is useful.
- Missing attributes: geometry, centroid, area, `tract_label`, `geotype`, and potentially population/household counts for ACS profiling.
- Assessment: solid for tract-centric modeling, but would benefit from richer geography context.

### HPISnapshot
- Business key correctness: `snapshot_id` is a good synthetic key and is uniquely constrained.
- Property completeness: required HPI fields are available; `source_type` exists.
- Duplicate risk: low, with no duplicate snapshot IDs present.
- Future compatibility: good for time-series and future snapshot-like datasets; can support additional metrics if properties are extended.
- Missing attributes: dataset lineage metadata, `hpi_standard_error`, `notes`, `hpi_available`, and classification flags.
- Assessment: suitable for HPI snapshots, with the caveat that provenance and dataset-level lineage are not modeled.

### ConformingLimitSnapshot
- Business key correctness: `snapshot_id` is appropriate and uniquely constrained.
- Property completeness: core conforming limit values exist; source metadata is present.
- Duplicate risk: low for the defined snapshot key.
- Future compatibility: adequate for future conforming-limit-style snapshots, and can extend to other loan limit or financial measure snapshots.
- Missing attributes: dataset lineage metadata, `max_limit` derivation is not stored explicitly, and `state_abbr` is represented by the source property `State` (inconsistent naming).
- Assessment: acceptable, but the snapshot node should standardize the state abbreviation property and add lineage support later.

## 2. Relationship design review

### State → County
- Cardinality: correct as 1 State to many Counties.
- Join keys: `State.state_fips` = `County.state_fips` is correct.
- Orphan risk: moderate only if county nodes are created from an incomplete county reference; current coverage appears good.
- Scalability: trivial at this size.
- Missing relationship: none.

### County → MetroArea
- Cardinality: correct as many Counties to one MetroArea.
- Join keys: `County.cbsa_number` = `MetroArea.cbsa_code` is appropriate, but note the relationship is only valid for counties with a CBSA code.
- Orphan risk: low in the current dataset, but future metro datasets should preserve CBSA normalization.
- Scalability: fine, though CBSA mapping may produce a many-to-one relationship fan-in.
- Missing relationship: possibly a reverse `MetroArea` → `County` containment/has-county relationship for semantic clarity.

### County → CensusTract
- Cardinality: correct as one County to many CensusTracts.
- Join keys: `County.county_fips` = `CensusTract.county_fips` is correct.
- Orphan risk: low if tract reference is complete and county nodes cover all county_fips.
- Scalability: good for 85k tracts.
- Missing relationship: none.

### CensusTract → HPISnapshot
- Cardinality: correct as one Tract to many HPISnapshots.
- Join keys: `CensusTract.tract_fips` = `HPISnapshot.tract_fips` is correct.
- Orphan risk: low based on current relationship coverage validation.
- Scalability: moderate; 2.18M snapshot nodes should be loaded in batches.
- Missing relationship: none.

### County → ConformingLimitSnapshot
- Cardinality: correct as one County to many ConformingLimitSnapshots.
- Join keys: `County.county_fips` = `ConformingLimitSnapshot.county_fips` is correct.
- Orphan risk: low with current coverage, but depends on county node completeness.
- Scalability: small, only ~10k snapshot nodes.
- Missing relationship: none.

## 3. Constraint review

- Every node has a unique business key constraint defined: `State`, `County`, `MetroArea`, `CensusTract`, `HPISnapshot`, `ConformingLimitSnapshot`.
- No unnecessary constraints are present.
- Future datasets should not violate these constraints if they adhere to the same business key definitions.
- Missing constraints:
  - no constraint or index for a composite snapshot business key such as `(tract_fips, year)` or `(county_fips, year)` besides the synthetic `snapshot_id`.
  - no referential integrity constraints can be expressed for relationships, but that is expected in Neo4j.
- Assessment: constraint coverage is sound, but consider explicit composite constraints if the synthetic snapshot ID strategy is not permanent.

## 4. Index review

- Existing indexes cover node lookup for `state_fips`, `state_abbr`, `county_fips`, `state_fips`, `cbsa_number`, `cbsa_code`, `tract_fips`, `county_fips`, `snapshot_id`, `year`, and `county_fips`.
- Relationship creation performance is supported by indexes on join keys.
- Future ACS joins at tract or county level are supported by `tract_fips` and `county_fips` indexes.
- Recommended additions:
  - composite index on `HPISnapshot(tract_fips, year)` for snapshot lookup and relationship creation, matching the mapping spec recommendation.
  - composite index on `ConformingLimitSnapshot(county_fips, year)` for efficient county-year snapshot lookups.
  - consider an index on `HPISnapshot.source_type` and `ConformingLimitSnapshot.source_type` if provenance queries are expected.
  - consider an index on `County.state_fips` if state-scoped queries are frequent, though it already exists.
- Assessment: index design is mostly good, but the current `indexes.cypher` file does not implement the composite indexes recommended by the mapping spec.

## 5. Load order review

- Dependency correctness: node order is correct; stable geography types load before snapshot types.
- Parent-before-child: correct for `State`→`County`, `County`→`CensusTract`, `CensusTract`→`HPISnapshot`.
- Relationship creation order is logical.
- Risks:
  - `County` node sourcing is derived from `conforming_limits`; if future county-only datasets arrive that do not align with conforming limits, a dedicated county reference source may be needed.
  - The plan loads `ConformingLimitSnapshot` after `County`, which is correct, but snapshot creation should also ensure county nodes are deduplicated by `county_fips` first.
- Assessment: load order is correct with a moderate risk around the canonical source of County nodes.

## 6. Scalability review

### Estimated graph size
- `State`: 56 nodes
- `MetroArea`: 994 nodes
- `County`: ~3,240 nodes
- `CensusTract`: 85,529 nodes
- `HPISnapshot`: 2,179,042 nodes
- `ConformingLimitSnapshot`: 9,703 nodes

### Assessment
- Memory considerations: the node counts are modest for state, metro, county, and tract. The main memory pressure will come from the 2.18M HPISnapshot nodes plus their relationships.
- Batch loading considerations: require batched ingestion for HPI snapshot creation and possibly relationship creation to avoid large transaction memory.
- Neo4j performance risks:
  - HPI snapshot count is the largest single concern; efficient batching and indexes will be important.
  - If future datasets add additional millions of snapshot nodes, the graph could grow significantly.
  - currently there is no explicit strategy for sharding or partitioning, but the size is still within an acceptable production range for a well-provisioned Neo4j instance.
- Assessment: manageable now, with moderate risk as snapshot volume grows.

## 7. Future dataset compatibility

### ACS
- The existing geographic backbone (`State`, `County`, `CensusTract`) is suitable for ACS ingestion.
- Future risk: ACS data may require additional tract-level attributes and a separate `ACSProfile` node or property model.
- Overall: compatible with extension, no redesign needed.

### FMR
- FMR is typically county- or metro-based, so the `County` and `MetroArea` nodes are appropriate.
- Future risk: FMR may use different metro definitions or non-CBSA metro areas; additional `MetroArea` metadata and alternative metro keys may be needed.
- Overall: compatible with minor extension.

### AMI
- AMI is usually metro-based and can attach to `MetroArea` or `County`.
- Future risk: AMI datasets may require a dedicated `AMI` node or a `market_area` abstraction.
- Overall: compatible; the backbone supports it.

### QCT
- QCT is tract-level and fits well with `CensusTract`.
- Future risk: QCT designation may require separate `QualifiedCensusTract` nodes or attributes on `CensusTract`.
- Overall: compatible.

### DDA
- DDA is also tract-level and can attach to `CensusTract`.
- Future risk: DDA designations may need separate status nodes or effective-date handling.
- Overall: compatible.

### LIHTC
- LIHTC project data will likely require a separate `LIHTCProject` node and relationships to `County`, `CensusTract`, and potentially `MetroArea`.
- Future risk: project-level entities and funding/program attributes are outside the current backbone, but the existing geography model supports them.
- Overall: compatible with an extension, not a redesign.

## 8. Strengths

- The graph backbone is clean and geography-driven.
- Node business keys are appropriate and constrained.
- Relationship cardinality is correct for the current datasets.
- Snapshot nodes are separated from stable geography nodes.
- The design is extensible for additional geographic datasets.

## 9. Weaknesses and risks

### Critical
- `indexes.cypher` does not implement the composite snapshot indexes that the mapping spec recommends, which weakens performance for snapshot-year lookups.
- `MetroArea` metadata is minimal; metro coverage is present but not robust for production analytics.

### High
- County nodes are derived from `conforming_limits` rather than a canonical county reference, creating a potential source-of-truth risk.
- `ConformingLimitSnapshot` uses the source property name `State` instead of a normalized `state_abbr` or `state_fips` attribute name.
- Lineage and provenance are not modeled; future production readiness will require a `DatasetSnapshot` or similar pattern.

### Medium
- `CensusTract` lacks geography enrichment such as centroids, area, and tract classification.
- `HPISnapshot` and `ConformingLimitSnapshot` lack explicit dataset lineage and optional metadata attributes.
- `State` lacks optional regional metadata for richer analytics.

### Low
- Naming consistency is slightly inconsistent (`cbsa_number` vs `cbsa_code`, `State` vs `state_abbr`).
- Relationship naming in the mapping spec is conceptually fine but may benefit from strict naming conventions.

## 9. Recommendations

- Add composite indexes for `HPISnapshot(tract_fips, year)` and `ConformingLimitSnapshot(county_fips, year)`.
- Enrich `MetroArea` with `cbsa_name` and supporting metadata before production usage.
- Create or source a dedicated county reference dataset for stable `County` node creation.
- Standardize snapshot state attributes by renaming `State` to `state_abbr` in `ConformingLimitSnapshot`.
- Plan for lineage modeling by introducing `DatasetSnapshot` nodes or datasource attributes.
- Add optional geographic attributes to `CensusTract` for future ACS/QCT/DDA use.

## Graph Design Readiness Score: 80/100

### Summary
The FHFA graph design is mostly production-ready as a geography-backed knowledge graph. The main improvement areas are index coverage, metro metadata, county source canonicalization, and provenance modeling. With those fixes, the design should be strong enough to support current and near-term future datasets.
