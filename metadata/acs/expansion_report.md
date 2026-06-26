# ACS Expansion Report

## Configuration Changes Applied

- Expanded `acs.years` to 2009-2024.
- Expanded `acs.enabled_tables` to 12 production tables.
- Populated 65 output-column to ACS-variable mappings.
- Kept recommended future tables registered but disabled.

## Expected Row Counts

- Bronze files: 9,792 JSON files (16 years x 12 tables x 51 states).
- Bronze data rows: about 16,421,568 table-state tract rows, assuming 85,529 tracts per year.
- Silver rows per table: about 1,368,464.
- Silver rows across all enabled tables: about 16,421,568.
- Gold rows: about 1,368,464 tract-year snapshots.
- Gold metric columns: 65 ACS metrics plus key columns.

## Full Run Commands

```powershell
venv\Scripts\python.exe -m src.ingestion.acs.downloaders.download_acs
venv\Scripts\python.exe -m src.ingestion.acs.validators.validate_bronze
venv\Scripts\python.exe -m src.ingestion.acs.transformers.transform_silver
venv\Scripts\python.exe -m src.ingestion.acs.builders.build_tract_acs_snapshot
```

## Future Extension

- To add a table: add variables under `tables.<TABLE>.variables`, set `implemented: true`, add its parquet path, add output fields to `gold.enabled_fields`, and include the table in `acs.enabled_tables`.
- To add/remove years: edit only `acs.years`.
