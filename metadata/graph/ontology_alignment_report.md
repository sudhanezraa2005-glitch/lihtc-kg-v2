# FHFA Neo4j Ontology Alignment Report

## Authoritative source

- `metadata/ontology/neo4j_mapping_spec.md`

## Relationship alignment

| Relationship before | Relationship after | Count impact |
| --- | --- | --- |
| `(:County)-[:BELONGS_TO]->(:State)` | `(:State)-[:CONTAINS]->(:County)` | Unchanged expected pair count; same join key `state_fips`. |
| `(:CensusTract)-[:BELONGS_TO]->(:County)` | `(:County)-[:CONTAINS]->(:CensusTract)` | Unchanged expected pair count; same join key `county_fips`. |
| `(:HPISnapshot)-[:MEASURES]->(:CensusTract)` | `(:CensusTract)-[:HAS_HPI]->(:HPISnapshot)` | Unchanged expected pair count; same join key `tract_fips`. |
| `(:ConformingLimitSnapshot)-[:APPLIES_TO]->(:County)` | `(:County)-[:HAS_CONFORMING_LIMIT]->(:ConformingLimitSnapshot)` | Unchanged expected pair count; same join key `county_fips`. |
| `(:County)-[:IN_METRO_AREA]->(:MetroArea)` | `(:County)-[:IN_METRO_AREA]->(:MetroArea)` | Unchanged; same join key `County.cbsa_number = MetroArea.cbsa_code`. |

## Files changed

- `src/graph/relationships/load_county_state.py`
- `src/graph/relationships/load_tract_county.py`
- `src/graph/relationships/load_hpi_tract.py`
- `src/graph/relationships/load_conforming_limit_county.py`
- `load_all_relationships.py`
- `src/graph/validation/validate_graph.py`
- `src/graph/graph_model.md`
- `src/graph/load_order.md`
- `metadata/ontology/neo4j_mapping_spec.md`
- `metadata/graph/ontology_alignment_report.md`

## Validation impact

- Relationship loaders now create only ontology-aligned relationships.
- Relationship validation now checks ontology relationship types and directions.
- Parent-to-child ontology relationships validate child coverage by requiring each eligible child node to have the matching incoming ontology relationship.
- `County` to `MetroArea` validation remains source-side because the relationship is optional for counties without `cbsa_number`.
- Relationship counts are expected to remain unchanged because all joins use the same business keys as before; only direction and relationship type changed.

## Verification

- Pyright: `0 errors, 0 warnings, 0 informations`.
- Python compile check passed for relationship loaders, validation scripts, and `load_all_relationships.py`.
- Source scan confirms implementation now references ontology relationship names:
  - `CONTAINS`
  - `HAS_HPI`
  - `HAS_CONFORMING_LIMIT`
  - `IN_METRO_AREA`
