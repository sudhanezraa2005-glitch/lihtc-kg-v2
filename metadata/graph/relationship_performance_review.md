# Relationship Loader Performance Review

## Scope

- `src/graph/relationships/base_relationship_loader.py`
- One-to-many ontology relationships:
  - `(:County)-[:CONTAINS]->(:CensusTract)`
  - `(:CensusTract)-[:HAS_HPI]->(:HPISnapshot)`
  - `(:County)-[:HAS_CONFORMING_LIMIT]->(:ConformingLimitSnapshot)`

## Existing approach

The prior relationship loader batched source nodes, matched all target nodes sharing the source join key, and passed only the source business key plus target join key into the write batch.

Write execution then re-expanded target nodes by join key:

```cypher
UNWIND $batch AS row
MATCH (s:Source {source_business_key: row.source_id})
MATCH (t:Target {target_join_key: row.target_id})
MERGE (s)-[:RELATIONSHIP]->(t)
```

### Performance profile

- Efficient for small many-to-one relationships.
- Expensive for one-to-many relationships because each source row can expand into many targets during write execution.
- For `CensusTract -> HPISnapshot`, every tract row may re-match many snapshot rows by `tract_fips`.
- For `County -> ConformingLimitSnapshot`, every county row may re-match many snapshot rows by `county_fips`.
- Batch size controlled source count, not concrete relationship-pair count.

## Optimized approach

The optimized loader batches concrete target nodes and returns one concrete source-target pair per relationship candidate:

```cypher
MATCH (t:Target)
WHERE t.target_business_key IS NOT NULL
  AND t.target_join_key IS NOT NULL
WITH t
ORDER BY t.target_business_key
SKIP $skip
LIMIT $limit
MATCH (s:Source {source_join_key: t.target_join_key})
RETURN
    s.source_business_key AS source_id,
    t.target_business_key AS target_id
```

Write execution now matches both nodes by indexed business keys:

```cypher
UNWIND $batch AS row
MATCH (s:Source {source_business_key: row.source_id})
MATCH (t:Target {target_business_key: row.target_id})
MERGE (s)-[:RELATIONSHIP]->(t)
```

### Performance profile

- Batch size now bounds concrete target nodes and therefore relationship candidates.
- Write execution no longer expands all children for a parent row.
- `MERGE` uses exact source and target node identity.
- Large one-to-many relationships scale linearly with target relationship count.

## Estimated impact

| Relationship | Existing approach | Optimized approach | Estimated impact |
| --- | --- | --- | --- |
| `County CONTAINS CensusTract` | Batch counties, expand tracts by `county_fips` during write. | Batch tracts, match county and tract by indexed keys. | Lower transaction fan-out; steadier memory use. |
| `CensusTract HAS_HPI HPISnapshot` | Batch tracts, expand HPI snapshots by `tract_fips` during write. | Batch HPI snapshots, match tract and snapshot by indexed keys. | Major improvement for multi-million snapshot loads. |
| `County HAS_CONFORMING_LIMIT ConformingLimitSnapshot` | Batch counties, expand conforming limit snapshots by `county_fips` during write. | Batch conforming limit snapshots, match county and snapshot by indexed keys. | Major improvement where yearly county snapshots are dense. |
| `State CONTAINS County` | Batch states, expand counties. | Batch counties, match state and county directly. | Minor improvement; small relationship count. |
| `County IN_METRO_AREA MetroArea` | Batch counties, match metro directly. | Batch metros and return concrete county-metro pairs. | Neutral to minor improvement; relationship count is small. |

## Validation

- Pyright: `0 errors, 0 warnings, 0 informations`.
- Compile check passed for `src/graph/relationships` and `load_all_relationships.py`.
- Relationship constants sanity check confirmed ontology names and directions are preserved:
  - `State CONTAINS County`
  - `County CONTAINS CensusTract`
  - `CensusTract HAS_HPI HPISnapshot`
  - `County HAS_CONFORMING_LIMIT ConformingLimitSnapshot`
  - `County IN_METRO_AREA MetroArea`

## Notes

- Ontology was not changed.
- Business keys were not changed.
- Node labels were not changed.
- Batch execution is preserved.
