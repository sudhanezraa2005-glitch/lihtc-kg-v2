# HUD FMR Data Lineage Documentation

Lineage:

```text
Bronze FMR
-> Silver FMR
-> Gold FMRSnapshot
-> Neo4j FMRSnapshot
-> County HAS_FMR FMRSnapshot
```

Stages:

1. Bronze validation reads Standard FMR workbooks and reports schema/data issues.
2. Silver transformation normalizes all years into a county-year keyed parquet dataset.
3. Gold enrichment renames rent fields into graph-ready FMRSnapshot properties.
4. Neo4j node loader merges `FMRSnapshot` nodes by `snapshot_id`.
5. Relationship loader creates `County HAS_FMR FMRSnapshot` relationships by `county_fips`.
6. Graph validation checks node duplicate keys, relationship coverage, duplicate relationships, and semantic mismatches.

