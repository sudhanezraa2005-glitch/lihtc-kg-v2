# HUD FMR Bronze Validation Documentation

Validator:

```powershell
venv\Scripts\python.exe -m src.ingestion.hud.validators.validate_fmr_bronze
```

Default input:

- Preferred: `data/bronze/hud/fmr/`
- Repository fallback: `data/bronze/fmr/`

Default report:

- `metadata/hud_fmr/fmr_bronze_validation_summary.md`

Checks:

- Standard FMR workbook discovery only; SAFMR and ERAP workbooks are ignored.
- Excel workbook readability using temporary metadata repair when needed.
- Required FMR concepts across renamed year-specific columns.
- 10-digit FIPS format.
- HUD area code presence and basic formatting.
- Duplicate 10-digit FIPS rows per workbook.
- Null rent values in `fmr_0` through `fmr_4`.
- Schema drift summary across fiscal years.

