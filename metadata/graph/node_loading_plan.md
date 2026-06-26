# Neo4j Node Loading Plan

## Overview

This document describes the node loading sequence, data sources, expected volumes, and configuration for the FHFA knowledge graph.

---

## Load Sequence

Nodes are loaded in dependency order to ensure parent nodes exist before child nodes are created (and before relationships are established).

### 1. State (no dependencies)
- **Node Label**: `State`
- **Source Dataset**: `data/gold/geography/states.parquet`
- **Business Key**: `state_fips` (unique identifier)
- **Key Properties**: 
  - `state_abbr` (two-letter abbreviation)
  - `state_name` (full state name)
- **Batch Size**: 1,000 records per batch
- **Expected Node Count**: 56 nodes (50 US states + 6 territories)
- **Load Strategy**: MERGE on `state_fips` for idempotency
- **Notes**: Small dataset; can be loaded in a single batch. No external dependencies.

### 2. MetroArea (no dependencies)
- **Node Label**: `MetroArea`
- **Source Dataset**: `data/gold/geography/metro_areas.parquet`
- **Business Key**: `cbsa_code` (Census Bureau Statistical Area code)
- **Key Properties**: 
  - `cbsa_code` (unique CBSA identifier)
- **Batch Size**: 1,000 records per batch
- **Expected Node Count**: 994 nodes (metropolitan and micropolitan areas)
- **Load Strategy**: MERGE on `cbsa_code` for idempotency
- **Notes**: Small dataset. MetroArea metadata is minimal; future enrichment planned for FMR/AMI onboarding. No external dependencies.

### 3. County (depends on State for validation)
- **Node Label**: `County`
- **Source Dataset**: `data/silver/fhfa/conforming_limits.parquet`
- **Business Key**: `county_fips` (unique 5-digit FIPS code)
- **Key Properties**: 
  - `state_fips` (reference to parent State)
  - `county_code` (state + county FIPS code)
  - `county_name` (full county name)
  - `cbsa_number` (optional reference to MetroArea)
- **Batch Size**: 5,000 records per batch
- **Expected Node Count**: ~3,240 unique counties (deduplicated from conforming_limits)
- **Load Strategy**: MERGE on `county_fips` with deduplication on first occurrence
- **Notes**: 
  - County nodes are sourced from `conforming_limits` because it provides richer metadata (`county_name`, `cbsa_number`) than `tract_reference`.
  - Conforming limits dataset contains multiple records per county (one per year), so deduplication is required.
  - Only ~94% of US counties are present (coverage based on conforming limit thresholds).

### 4. CensusTract (depends on County for validation)
- **Node Label**: `CensusTract`
- **Source Dataset**: `data/silver/geography/tract_reference.parquet`
- **Business Key**: `tract_fips` (unique 11-digit FIPS code: state + county + tract)
- **Key Properties**: 
  - `county_fips` (reference to parent County)
  - `state_fips` (reference to State)
  - `county_code` (state + county FIPS)
  - `tract_code` (tract identifier within county)
  - `tract_name` (label or description)
- **Batch Size**: 5,000 records per batch
- **Expected Node Count**: ~85,500 unique tracts (deduplicated)
- **Load Strategy**: MERGE on `tract_fips` with deduplication on first occurrence
- **Notes**: 
  - Census tract reference is the canonical source for stable census geography.
  - Tract reference includes all tracts in the US with census data coverage.
  - No temporal aspects; tract boundaries are stable across years.

### 5. ConformingLimitSnapshot (depends on County for relationships)
- **Node Label**: `ConformingLimitSnapshot`
- **Source Dataset**: `data/silver/fhfa/conforming_limits.parquet`
- **Business Key**: `snapshot_id` (synthetic key: county_fips + year)
- **Key Properties**: 
  - `county_fips` (reference for HAS_CONFORMING_LIMIT relationship)
  - `state_fips` (denormalized for performance)
  - `state_abbr` (state abbreviation for context)
  - `year` (temporal dimension)
  - `limit_1_unit`, `limit_2_unit`, `limit_3_unit`, `limit_4_unit` (loan limit thresholds)
  - `source_type` (data source lineage)
- **Batch Size**: 5,000 records per batch
- **Expected Node Count**: 9,703 snapshots (one per county-year combination)
- **Load Strategy**: MERGE on `snapshot_id` for idempotency
- **Cardinality**: Perfect 1:1 on (county_fips, year)
- **Notes**: 
  - Temporal snapshot node; represents a point-in-time conforming limit definition.
  - Composite index on (county_fips, year) enables efficient temporal lookups.
  - All conforming limit rows represent unique snapshots (no duplicates).

### 6. HPISnapshot (depends on CensusTract for relationships)
- **Node Label**: `HPISnapshot`
- **Source Dataset**: `data/gold/fhfa/tract_hpi_enriched.parquet`
- **Business Key**: `snapshot_id` (synthetic key: tract_fips + year)
- **Key Properties**: 
  - `tract_fips` (reference for HAS_HPI relationship)
  - `county_fips` (denormalized reference)
  - `state_fips` (denormalized for performance)
  - `year` (temporal dimension)
  - `hpi` (house price index value)
  - `annual_change` (annual percentage change)
  - `hpi1990`, `hpi2000` (historical baseline indices)
  - `source_type` (data source lineage)
- **Batch Size**: 10,000 records per batch
- **Expected Node Count**: 2,179,042 snapshots (one per tract-year combination)
- **Load Strategy**: MERGE on `snapshot_id` for idempotency
- **Cardinality**: Perfect 1:1 on (tract_fips, year)
- **Notes**: 
  - Largest dataset; requires efficient batching and indexing.
  - Composite index on (tract_fips, year) enables efficient temporal lookups.
  - Spans approximately 50 years of historical HPI data (1968-2025).
  - All HPI snapshot rows represent unique snapshots (no duplicates).
  - Batch processing is essential to manage memory and transaction size.

---

## Load Configuration

### Batch Sizes (Configurable)

| Node Type | Default Batch Size | Rationale |
|-----------|-------------------|-----------|
| State | 1,000 | Small dataset; simple properties |
| MetroArea | 1,000 | Small dataset; simple properties |
| County | 5,000 | Medium dataset; moderate deduplication |
| CensusTract | 5,000 | Larger dataset; moderate deduplication |
| ConformingLimitSnapshot | 5,000 | Medium dataset; temporal properties |
| HPISnapshot | 10,000 | Very large dataset; temporal properties; memory pressure |

### Expected Total Nodes

```
State:                      56 nodes
MetroArea:                  994 nodes
County:                     ~3,240 nodes
CensusTract:                ~85,500 nodes
ConformingLimitSnapshot:    9,703 nodes
HPISnapshot:                2,179,042 nodes
────────────────────────────────────
TOTAL:                      ~2,278,535 nodes
```

### Expected Load Time Estimates

Assuming typical Neo4j performance on a well-configured instance:

| Node Type | Expected Time | Notes |
|-----------|--------------|-------|
| State | < 1 second | 56 nodes |
| MetroArea | < 1 second | 994 nodes |
| County | ~5-10 seconds | 3,240 nodes with deduplication |
| CensusTract | ~30-60 seconds | 85,500 nodes with deduplication |
| ConformingLimitSnapshot | ~30-60 seconds | 9,703 nodes; temporal properties |
| HPISnapshot | 15-30 minutes | 2,179,042 nodes; large volume; batching critical |
| **TOTAL** | **~20-35 minutes** | End-to-end load (excluding constraints/indexes) |

---

## Data Quality and Idempotency

### Key Principles

1. **MERGE on Business Key**: All loaders use MERGE on the business key to ensure idempotency. Re-running the loader should not create duplicate nodes.
2. **Deduplication**: County and CensusTract loaders deduplicate on their respective business keys (keeping the first occurrence).
3. **Perfect Cardinality**: Both snapshot types (HPISnapshot and ConformingLimitSnapshot) have perfect 1:1 cardinality on their composite business keys.
4. **Null Handling**: Properties with null values are skipped during property assignment to prevent null overwrites.

### Validation Checks

Before loading nodes into relationships, verify:

- [ ] All State nodes exist (count: 56)
- [ ] All MetroArea nodes exist (count: 994)
- [ ] All County nodes exist (~3,240)
- [ ] All CensusTract nodes exist (~85,500)
- [ ] All ConformingLimitSnapshot nodes exist (9,703)
- [ ] All HPISnapshot nodes exist (2,179,042)
- [ ] No duplicate nodes per business key
- [ ] All required properties are populated

---

## Load Execution

### Prerequisites

1. **Neo4j Configuration**: Set environment variables or provide arguments:
   - `NEO4J_URI`: Connection string (e.g., `bolt://localhost:7687`)
   - `NEO4J_USER`: Username (default: `neo4j`)
   - `NEO4J_PASSWORD`: Password

2. **Dependencies**: Install Python driver:
   ```bash
   pip install neo4j pandas pyarrow
   ```

3. **Constraints and Indexes**: Before loading nodes, create constraints and indexes:
   ```bash
   neo4j-cypher-shell -u neo4j -p <password> < src/graph/constraints.cypher
   neo4j-cypher-shell -u neo4j -p <password> < src/graph/indexes.cypher
   ```

### Running the Load

**Execute all nodes in sequence**:
```bash
python load_all_nodes.py \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password <password> \
  --data-dir data
```

**Or use environment variables**:
```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=<password>
python load_all_nodes.py --data-dir data
```

### Individual Loader Execution

To run a single loader (for testing or recovery):

```bash
python -c "
from src.graph.config.neo4j_config import Neo4jConfig
from src.graph.loaders.load_states import StateLoader

config = Neo4jConfig()
driver = config.get_driver()
loader = StateLoader(driver)
count = loader.load_from_parquet('data/gold/geography/states.parquet')
print(f'Loaded {count} State nodes')
driver.close()
"
```

---

## Monitoring and Logging

All loaders output structured logs with:
- Batch processing progress
- Record counts
- Error details (if any)

**Log Levels**:
- `INFO`: Batch completions, total node counts
- `DEBUG`: Detailed record-level operations (verbose)
- `ERROR`: Failures and exceptions

Monitor logs for:
- Batch completion rate (should be steady)
- Total node counts (should match expected)
- Null/empty property warnings (if any)
- Neo4j connection errors

---

## Next Steps

1. **Create constraints** using `src/graph/constraints.cypher`
2. **Create indexes** using `src/graph/indexes.cypher`
3. **Run node loaders** using `load_all_nodes.py`
4. **Verify node counts** against expected volumes
5. **Create relationships** (separate loader not included; documented in relationship loading plan)

---

## Troubleshooting

### Connection Failures
- Verify Neo4j is running: `neo4j-admin status`
- Check URI format (e.g., `bolt://localhost:7687`)
- Verify credentials and permissions

### Out of Memory Errors
- Reduce batch size for HPISnapshot (try 5,000)
- Increase Neo4j heap memory: `dbms.memory.heap.max_size=4G`

### Duplicate Node Errors
- Ensure constraints are created before loading
- Check for corrupted data in source parquet files

### Slow Load Times
- Verify indexes are created
- Check Neo4j transaction log for slow queries
- Consider increasing batch size for faster throughput

---

## References

- Graph model: `src/graph/graph_model.md`
- Mapping spec: `metadata/ontology/neo4j_mapping_spec.md`
- Constraints: `src/graph/constraints.cypher`
- Indexes: `src/graph/indexes.cypher`
- Preload validation: `metadata/graph/preload_fix_validation.md`
