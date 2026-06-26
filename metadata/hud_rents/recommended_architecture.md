# HUD Rent Architecture Recommendation

Recommendation: Option C

Create all three snapshot node families:

- `FMRSnapshot`
- `SAFMRSnapshot`
- `ERAPSnapshot`

## Justification

The Bronze files contain three materially different products:

- Standard FMR exists for FY2018-FY2026 and uses 10-digit FIPS/HUD area rows.
- SAFMR exists for FY2019-FY2026 and uses ZIP/ZCTA plus HUD area rows.
- ERAP exists for FY2022-FY2024 and uses ZIP plus HUD area rows, with ERAP-specific rent columns and different HUD area cardinality.

Using only `FMRSnapshot` would collapse ZIP-level and county/HUD-area level products into one label with weak semantics. Using only `FMRSnapshot` plus `SAFMRSnapshot` would force ERAP into SAFMR even though the ERAP columns, year coverage, and area cardinality differ.

## Architecture Decision

Use separate ingestion pipelines and graph labels by dataset type:

| Dataset | Silver table | Gold table | Graph node |
| --- | --- | --- | --- |
| Standard FMR | `data/silver/hud/fmr.parquet` | `data/gold/hud/fmr_snapshots.parquet` | `FMRSnapshot` |
| SAFMR | `data/silver/hud/safmr.parquet` | `data/gold/hud/safmr_snapshots.parquet` | `SAFMRSnapshot` |
| ERAP | `data/silver/hud/erap.parquet` | `data/gold/hud/erap_snapshots.parquet` | `ERAPSnapshot` |

## Design Principles

- Preserve dataset type as a first-class semantic distinction.
- Normalize source column variants in Silver, not in graph loaders.
- Keep business keys deterministic and dataset-specific.
- Do not infer county relationships from ZIP-level files without a crosswalk.
- Add `ZIPCode` as a reference node only if SAFMR/ERAP graph loading is required.
- Consider a future `HUDArea` reference node to preserve HUD-specific area definitions that do not equal existing `MetroArea` nodes.

