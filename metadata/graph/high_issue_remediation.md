# FHFA Neo4j High-Issue Remediation

## Files changed

- `src/graph/loaders/base_loader.py`
- `src/graph/validation/validate_graph.py`
- `metadata/graph/high_issue_remediation.md`

## Remediation summary

### Pandas and numpy value normalization

Added `normalize_value()` and applied it in `BaseLoader._prepare_properties()`.

Conversions:

- `numpy.int*` -> Python `int`
- `numpy.float*` -> Python `float`
- `numpy.bool_` -> Python `bool`
- `pandas.Timestamp` -> Python `datetime`
- `NaN`, `pandas.NA`, and null-like values -> omitted from Neo4j property maps

### Semantic relationship validation

Graph validation now checks semantic join-key consistency for every ontology relationship:

- `State.state_fips == County.state_fips`
- `County.county_fips == CensusTract.county_fips`
- `CensusTract.tract_fips == HPISnapshot.tract_fips`
- `County.county_fips == ConformingLimitSnapshot.county_fips`
- `County.cbsa_number == MetroArea.cbsa_code`

The metro validation preserves the existing ontology and node schema, where the County metro join property is `cbsa_number`.

Validation output now includes `Semantic mismatches`, and `READY_FOR_FULL_LOAD` is false when any mismatch is present.

## Tests executed

- `venv\Scripts\pyright.exe`
- `venv\Scripts\python.exe -m compileall src\graph\loaders src\graph\validation`
- Runtime smoke test for `normalize_value()`:
  - `numpy.int64`
  - `numpy.float64`
  - `numpy.bool_`
  - `numpy.nan`
  - `pandas.NA`
  - `pandas.Timestamp`

## Validation results

- Pyright: `0 errors, 0 warnings, 0 informations`
- Compile check: passed
- `normalize_value()` smoke test: passed
- Graph validation script now verifies relationship coverage, duplicate relationships, and semantic join-key mismatches.

No ontology files were modified.
No node labels were modified.
No business keys were changed.
