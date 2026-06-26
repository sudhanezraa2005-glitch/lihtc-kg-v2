# HUD Rent Implementation Roadmap

This roadmap is intentionally design-only. No ingestion implementation has been added.

## Phase 2B Finalization

1. Approve Option C architecture.
2. Confirm graph ontology naming for `FMRSnapshot`, `SAFMRSnapshot`, `ERAPSnapshot`, `ZIPCode`, and optional `HUDArea`.
3. Decide whether FMR should connect directly to `County` only, or also to `State`, `MetroArea`, and future `HUDArea`.

## Phase 2C Reference Data

1. Add or source ZIP reference data if SAFMR/ERAP graph loading is required.
2. Select a ZIP-to-county crosswalk strategy before creating county relationships from SAFMR/ERAP.
3. Validate HUD area code parsing rules for `METRO...`, `NCNTY...`, and other observed patterns.
4. Decide whether to model `HUDArea` explicitly to avoid overloading `MetroArea`.

## Phase 2D Silver Build

1. Implement Bronze readers that tolerate workbook metadata issues without modifying Bronze files.
2. Implement FMR Silver transformer.
3. Implement SAFMR Silver transformer.
4. Implement ERAP Silver transformer.
5. Add schema validation for required columns, renamed columns, datatypes, and uniqueness.
6. Write Silver parquet outputs under `data/silver/hud/`.

## Phase 2E Gold Build

1. Implement graph-ready Gold transformers for each snapshot type.
2. Generate deterministic business keys.
3. Add relationship join columns.
4. Validate no duplicate business keys.
5. Write Gold parquet outputs under `data/gold/hud/`.

## Phase 2F Graph Layer

1. Extend ontology only after design approval.
2. Add constraints and indexes for new labels.
3. Add node loaders for approved snapshot labels.
4. Add relationship loaders only for validated relationships.
5. Extend graph validation with rent snapshot coverage checks.

## Phase 2G Validation

1. Validate row counts against Bronze inventory.
2. Validate per-year coverage.
3. Validate uniqueness by business key.
4. Validate ZIP references if ZIP nodes are introduced.
5. Validate county/metro relationships only when crosswalks are available.

## Recommended Build Order

1. `ZIPCode` / `HUDArea` reference decision.
2. Silver FMR.
3. Silver SAFMR.
4. Silver ERAP.
5. Gold FMR.
6. Gold SAFMR.
7. Gold ERAP.
8. Ontology extension.
9. Neo4j constraints/indexes.
10. Loaders and relationship loaders.
11. Graph validation.

