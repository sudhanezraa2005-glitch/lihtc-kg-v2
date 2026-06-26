# Neo4j Schema Bootstrap Report

## Files created

- `src/graph/setup/apply_constraints.py`
- `src/graph/setup/apply_indexes.py`
- `src/graph/setup/validate_schema.py`
- `src/graph/setup/__init__.py`
- `metadata/graph/schema_bootstrap_report.md`

## Files updated

- `load_all_nodes.py`
- `pyrightconfig.json`

## Bootstrap behavior

1. Read `src/graph/constraints.cypher`.
2. Execute all constraint statements.
3. Verify required constraints with `SHOW CONSTRAINTS`.
4. Read `src/graph/indexes.cypher`.
5. Execute all index statements.
6. Verify required indexes with `SHOW INDEXES`.
7. Fail if any required constraint or index is missing.

## Required schema parsed from source files

### Constraints

- `State(state_fips)`
- `County(county_fips)`
- `MetroArea(cbsa_code)`
- `CensusTract(tract_fips)`
- `HPISnapshot(snapshot_id)`
- `ConformingLimitSnapshot(snapshot_id)`

### Indexes

- `State(state_fips)`
- `State(state_abbr)`
- `County(county_fips)`
- `County(state_fips)`
- `County(cbsa_number)`
- `MetroArea(cbsa_code)`
- `CensusTract(tract_fips)`
- `CensusTract(county_fips)`
- `HPISnapshot(snapshot_id)`
- `HPISnapshot(year)`
- `HPISnapshot(tract_fips)`
- `HPISnapshot(tract_fips, year)`
- `ConformingLimitSnapshot(snapshot_id)`
- `ConformingLimitSnapshot(year)`
- `ConformingLimitSnapshot(county_fips)`
- `ConformingLimitSnapshot(county_fips, year)`

## Updated production execution order

`load_all_nodes.py` now executes:

1. Apply constraints
2. Apply indexes
3. Validate schema
4. Load nodes
5. Load relationships
6. Run graph validation

## Validation performed

- Pyright: `0 errors, 0 warnings, 0 informations`
- Compile check passed for `src/graph/setup` and `load_all_nodes.py`
- CLI help checks passed for:
  - `python -m src.graph.setup.apply_constraints --help`
  - `python -m src.graph.setup.apply_indexes --help`
  - `python -m src.graph.setup.validate_schema --help`
- Parser smoke check found:
  - 6 required constraints
  - 16 required indexes

## Notes

- No ontology files were changed.
- Schema validation is read-only.
- Constraint and index application are idempotent because the Cypher files use `IF NOT EXISTS`.
