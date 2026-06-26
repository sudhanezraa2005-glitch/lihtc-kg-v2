# Pre-Loader Remediation for Neo4j

This document extracts only the critical and high findings from `metadata/graph/graph_design_review.md` and maps them to actionable pre-loader remediation items.

## Findings

### 1. Missing composite snapshot indexes in `indexes.cypher`
1. Issue description
   - The current `src/graph/indexes.cypher` file does not implement the composite snapshot indexes recommended by the mapping spec.
2. Why it matters
   - Without these indexes, snapshot lookups by year and geography become slower and can degrade relationship creation performance during ingestion.
3. Impact on Neo4j loading
   - Loading HPISnapshot and ConformingLimitSnapshot nodes plus their relationships will be less efficient and may require larger transactions or slower match operations.
4. Recommended fix
   - Add composite indexes for `HPISnapshot(tract_fips, year)` and `ConformingLimitSnapshot(county_fips, year)` before loading.
5. Effort estimate
   - Medium

### 2. Minimal `MetroArea` metadata
1. Issue description
   - `MetroArea` nodes currently contain only the canonical `cbsa_code` and lack descriptive metadata such as `cbsa_name`, `metro_type`, and related state or population attributes.
2. Why it matters
   - Sparse metro metadata limits analytics, makes validation harder, and reduces the usefulness of metro-level relationships for downstream business queries.
3. Impact on Neo4j loading
   - The graph can still load, but the metro backbone will be weak and may require a second pass to enrich or correct metro nodes.
4. Recommended fix
   - Enrich `MetroArea` node creation with supporting metadata before production use, ideally from a dedicated CBSA reference dataset.
5. Effort estimate
   - Medium

### 3. County nodes derived from `conforming_limits` instead of a dedicated county reference
1. Issue description
   - County nodes are being sourced from the `conforming_limits` dataset rather than a canonical county reference dataset.
2. Why it matters
   - This creates a source-of-truth risk: the county node set may be incomplete, inconsistent, or tied to conforming limit coverage rather than stable geography.
3. Impact on Neo4j loading
   - If county nodes are incomplete or inconsistent, snapshot relationships and county-based joins may fail or produce orphaned nodes during ingestion.
4. Recommended fix
   - Source `County` nodes from a dedicated county reference dataset and deduplicate on `county_fips` before loading.
5. Effort estimate
   - Large

### 4. Inconsistent `ConformingLimitSnapshot` state property naming
1. Issue description
   - `ConformingLimitSnapshot` uses the source property name `State` instead of a standardized property such as `state_abbr` or `state_fips`.
2. Why it matters
   - Inconsistent property naming creates confusion, complicates query logic, and reduces compatibility with other graph datasets and ingestion patterns.
3. Impact on Neo4j loading
   - Misnamed properties can propagate through loaders and require corrective updates after load, increasing rework and error risk.
4. Recommended fix
   - Normalize the snapshot property name to `state_abbr` or add `state_fips` prior to loading the conforming limit snapshot nodes.
5. Effort estimate
   - Small

### 5. Lineage and provenance are not modeled
1. Issue description
   - The current graph design does not model dataset lineage or provenance, such as a `DatasetSnapshot` node or datasource attributes.
2. Why it matters
   - Without lineage metadata, it is harder to trace data origins, validate historical source quality, or audit ingestion results for compliance.
3. Impact on Neo4j loading
   - This issue does not block loading, but it leaves the graph without provenance structure and can make future debugging and data governance more difficult.
4. Recommended fix
   - Introduce a lineage model such as `DatasetSnapshot` nodes or attach datasource attributes to snapshot nodes after initial loading.
5. Effort estimate
   - Medium

## Must Fix Before Neo4j
- Add composite snapshot indexes for `HPISnapshot(tract_fips, year)` and `ConformingLimitSnapshot(county_fips, year)`.
- Source `County` nodes from a dedicated county reference dataset and deduplicate on `county_fips`.
- Normalize `ConformingLimitSnapshot` state properties to `state_abbr` or `state_fips`.

## Can Fix After Neo4j
- Enrich `MetroArea` metadata with `cbsa_name`, `metro_type`, state linkages, and other attributes.
- Model lineage/provenance by adding `DatasetSnapshot` nodes or datasource attributes.
