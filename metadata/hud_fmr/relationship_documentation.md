# HUD FMR Relationship Documentation

Implemented relationship:

```cypher
(:County)-[:HAS_FMR]->(:FMRSnapshot)
```

Join rule:

- `County.county_fips = FMRSnapshot.county_fips`

Relationship loader:

```powershell
venv\Scripts\python.exe -m src.graph.relationships.load_county_fmr
```

Deferred relationships:

- No `MetroArea` FMR relationship is implemented.
- No `HUDArea` node is implemented.
- No SAFMR or ERAP graph relationship is implemented.

