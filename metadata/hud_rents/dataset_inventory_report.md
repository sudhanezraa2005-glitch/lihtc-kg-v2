# HUD Rent Dataset Inventory Report

Generated from files present in `data/bronze/fmr` on 2026-06-19. No ingestion code was implemented.

## Summary

| Dataset type | Years present | File count | Total rows |
| --- | --- | ---: | ---: |
| FMR | 2018-2026 | 9 | 42,889 |
| SAFMR | 2019-2026 | 8 | 265,146 |
| ERAP | 2022-2024 | 3 | 87,984 |
| Unknown | None | 0 | 0 |

## Inventory

| File | Year | Type | Sheet | Rows | Columns | Primary geographic level |
| --- | ---: | --- | --- | ---: | ---: | --- |
| `data/bronze/fmr/FY18_4050_FMRs_rev.xlsx` | 2018 | FMR | `FMR18_INFO` | 4,769 | 20 | 10-digit FIPS row; county FIPS extractable; HUD area present |
| `data/bronze/fmr/FY2019_4050_FMRs_rev2.xlsx` | 2019 | FMR | `fmr19_info` | 4,767 | 20 | 10-digit FIPS row; county FIPS extractable; HUD area present |
| `data/bronze/fmr/FY20_4050_FMRs_rev.xlsx` | 2020 | FMR | `FMR20_INFO` | 4,766 | 20 | 10-digit FIPS row; county FIPS extractable; HUD area present |
| `data/bronze/fmr/FY21_4050_FMRs_rev.xlsx` | 2021 | FMR | `FMR21_INFO` | 4,766 | 16 | 10-digit FIPS row; county FIPS extractable; HUD area present |
| `data/bronze/fmr/FY22_FMRs_revised.xlsx` | 2022 | FMR | `FY22_FMRs_revised` | 4,765 | 14 | 10-digit FIPS row; county FIPS extractable; HUD area present |
| `data/bronze/fmr/FY23_FMRs_revised.xlsx` | 2023 | FMR | `FY23_FMRs_revised` | 4,764 | 14 | 10-digit FIPS row; county FIPS extractable; HUD area present |
| `data/bronze/fmr/FMR2024_final_revised.xlsx` | 2024 | FMR | `FY24_FMRs_rev` | 4,764 | 14 | 10-digit FIPS row; county FIPS extractable; HUD area present |
| `data/bronze/fmr/FY25_FMRs_revised.xlsx` | 2025 | FMR | `FY25_FMRs_revised` | 4,764 | 14 | 10-digit FIPS row; county FIPS extractable; HUD area present |
| `data/bronze/fmr/FY26_FMRs_revised.xlsx` | 2026 | FMR | `FY26_FMRs_revised` | 4,764 | 14 | 10-digit FIPS row; county FIPS extractable; HUD area present |
| `data/bronze/fmr/fy2019_safmrs_rev.xlsx` | 2019 | SAFMR | `SAFMRS` | 26,019 | 18 | ZIP Code plus HUD area |
| `data/bronze/fmr/fy2020_safmrs_rev.xlsx` | 2020 | SAFMR | `SAFMRS` | 26,090 | 18 | ZCTA plus HUD area |
| `data/bronze/fmr/fy2021_safmrs_revised.xlsx` | 2021 | SAFMR | `SAFMRs` | 27,144 | 18 | ZIP Code plus HUD area |
| `data/bronze/fmr/fy2022_safmrs_revised.xlsx` | 2022 | SAFMR | `SAFMRs` | 27,322 | 18 | ZIP Code plus HUD area |
| `data/bronze/fmr/fy2023_safmrs_revised.xlsx` | 2023 | SAFMR | `SAFMRs` | 27,331 | 18 | ZIP Code plus HUD area |
| `data/bronze/fmr/fy2024_safmrs_revised.xlsx` | 2024 | SAFMR | `SAFMRs` | 27,446 | 18 | ZIP Code plus HUD area |
| `data/bronze/fmr/fy2025_safmrs_revised (1).xlsx` | 2025 | SAFMR | `SAFMRs` | 51,899 | 18 | ZIP Code plus HUD area |
| `data/bronze/fmr/fy2026_safmrs_revised.xlsx` | 2026 | SAFMR | `SAFMRs` | 51,895 | 18 | ZIP Code plus HUD area |
| `data/bronze/fmr/fy2022_erap_fmrs_revised.xlsx` | 2022 | ERAP | `ERAP_FMRs` | 29,283 | 8 | ZIP Code plus HUD area |
| `data/bronze/fmr/fy2023_erap_fmrs_revised.xlsx` | 2023 | ERAP | `SAFMRs` | 29,293 | 8 | ZIP Code plus HUD area |
| `data/bronze/fmr/fy2024_erap_fmrs_revised.xlsx` | 2024 | ERAP | `ERAP FMRs` | 29,408 | 8 | ZIP Code plus HUD area |

## Observations

- FMR files exist for every FY2018-FY2026 year.
- SAFMR files begin in FY2019 and continue through FY2026; no FY2018 SAFMR file is present.
- ERAP files are present only for FY2022-FY2024.
- No files were classified as Unknown.
- Several Excel files required temporary metadata repair for audit reading because workbook core properties contain invalid timestamp text. Bronze files were not modified.

