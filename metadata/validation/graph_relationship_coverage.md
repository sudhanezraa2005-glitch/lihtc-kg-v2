# Graph Relationship Coverage Validation

This report validates the current FHFA relationship coverage against the stable geography and snapshot datasets.

## Relationship coverage summary

### 1. Every CensusTract maps to exactly one County
- Unique CensusTracts: 85529
- Exactly one county mapping: 85529
- Multiple county mappings: 0
- Orphan tracts (zero county mapping): 0
- Coverage: 100.00%

### 2. Every County maps to exactly one State
- Unique Counties in tract reference: 3243
- Exactly one state mapping: 3243
- Multiple state mappings: 0
- Coverage: 100.00%

### 3. Every HPISnapshot maps to exactly one CensusTract
- HPISnapshot rows: 2179042
- Valid tract references: 2179042
- Orphan HPISnapshots: 0
- Coverage: 100.00%

### 4. Every ConformingLimitSnapshot maps to exactly one County
- ConformingLimitSnapshot rows: 9703
- Valid county references (derived county domain): 9703
- Orphan ConformingLimitSnapshots: 0
- Coverage: 100.00%

### 5. Every County CBSA code maps to a MetroArea
- Unique CBSA codes in conforming limits: 994
- Missing CBSA mappings: 0
- Rows with orphan CBSA code: 0
- Coverage: 100.00%

## Orphan records and duplicates

- Tract Reference duplicate tract_fips rows: 0
- State duplicate state_fips rows: 0
- MetroArea duplicate cbsa_code rows: 0
- HPISnapshot duplicate business keys (tract_fips+year): 0
- ConformingLimitSnapshot duplicate business keys (county_fips+year): 0

## Detected orphan examples

- No tracts with multiple county mappings detected.

- No orphan HPISnapshots detected.

- No orphan ConformingLimitSnapshots detected.

- No orphan CBSA codes detected.

## Graph readiness assessment

- Graph readiness status: READY

All relationship coverage checks passed.