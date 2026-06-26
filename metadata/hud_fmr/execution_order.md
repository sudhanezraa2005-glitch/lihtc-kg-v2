# HUD FMR Execution Order

Run commands from the repository root.

1. Validate Bronze FMR workbooks.

```powershell
venv\Scripts\python.exe -m src.ingestion.hud.validators.validate_fmr_bronze
```

2. Transform Bronze FMR to Silver.

```powershell
venv\Scripts\python.exe -m src.ingestion.hud.transformers.transform_fmr
```

3. Enrich Silver FMR to Gold.

```powershell
venv\Scripts\python.exe -m src.ingestion.hud.transformers.enrich_fmr
```

4. Apply Neo4j constraints and indexes.

```powershell
venv\Scripts\python.exe -m src.graph.setup.apply_constraints
venv\Scripts\python.exe -m src.graph.setup.apply_indexes
venv\Scripts\python.exe -m src.graph.setup.validate_schema
```

5. Load FMR snapshot nodes.

```powershell
venv\Scripts\python.exe -m src.graph.loaders.load_fmr_snapshots
```

6. Load County-to-FMR relationships.

```powershell
venv\Scripts\python.exe -m src.graph.relationships.load_county_fmr
```

7. Run graph validation.

```powershell
venv\Scripts\python.exe -m src.graph.validation.validate_graph
```

