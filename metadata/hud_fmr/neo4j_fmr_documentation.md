# HUD FMR Neo4j Documentation

Node:

```cypher
(:FMRSnapshot {
  snapshot_id,
  county_fips,
  state_fips,
  year,
  studio_rent,
  one_bedroom_rent,
  two_bedroom_rent,
  three_bedroom_rent,
  four_bedroom_rent,
  hud_area_code,
  hud_area_name,
  source_type
})
```

Constraint:

```cypher
CREATE CONSTRAINT IF NOT EXISTS FOR (f:FMRSnapshot) REQUIRE f.snapshot_id IS UNIQUE;
```

Indexes:

```cypher
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.snapshot_id);
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.county_fips);
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.state_fips);
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.year);
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.county_fips, f.year);
```

Loader:

```powershell
venv\Scripts\python.exe -m src.graph.loaders.load_fmr_snapshots
```

