# ACS Ingestion Architecture

Scope implemented now:

- Dataset: ACS 5-Year Estimates
- Geography: Census tract
- Year: 2024
- Table: B19013
- Field: `median_household_income`

No Neo4j loaders, relationships, or validation scripts are implemented.

## Flow

```text
ACS API
-> data/bronze/acs/{year}/{table}/{state}.json
-> data/silver/acs/{table}.parquet
-> data/gold/acs/tract_acs_snapshot.parquet
```

## Files Created

- `metadata/acs/table_registry.yaml`
- `src/ingestion/acs/registry.py`
- `src/ingestion/acs/downloaders/download_acs.py`
- `src/ingestion/acs/validators/validate_bronze.py`
- `src/ingestion/acs/transformers/transform_silver.py`
- `src/ingestion/acs/builders/build_tract_acs_snapshot.py`

## How To Run

Bronze download:

```powershell
venv\Scripts\python.exe -m src.ingestion.acs.downloaders.download_acs
```

Bronze validation:

```powershell
venv\Scripts\python.exe -m src.ingestion.acs.validators.validate_bronze
```

Silver transform:

```powershell
venv\Scripts\python.exe -m src.ingestion.acs.transformers.transform_silver
```

Gold build:

```powershell
venv\Scripts\python.exe -m src.ingestion.acs.builders.build_tract_acs_snapshot
```

## Storage Estimate

Pilot B19013 2024:

- Bronze JSON: roughly 10-30 MB for all states.
- Silver parquet: roughly 1-5 MB.
- Gold parquet: roughly 1-5 MB.

Full 2009-2024 expansion with many tables:

- Bronze JSON: likely 2-10 GB depending variable count.
- Silver parquet: likely 300 MB-2 GB.
- Gold parquet: likely 300 MB-2 GB.

## Extension Path

To expand 2024 to 2009-2024:

1. Edit `metadata/acs/table_registry.yaml`.
2. Change `acs.years` from `[2024]` to `2009` through `2024`.
3. Run Bronze, validation, Silver, and Gold commands again.

To expand B19013 to all approved tables:

1. Add variable mappings under each table in `metadata/acs/table_registry.yaml`.
2. Add desired output field names to `gold.enabled_fields`.
3. Add table IDs to `acs.enabled_tables`.
4. Run the same four commands.

The code reads years, states, tables, variables, and Gold fields from the registry.

