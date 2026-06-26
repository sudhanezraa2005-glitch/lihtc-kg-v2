# HUD FMR Bronze Validation Summary

- Generated at: `2026-06-19T11:03:35.713919+00:00`
- Source directory: `data\bronze\fmr`
- Files validated: 9
- Schema variants detected: 9
- BRONZE_FMR_READY = TRUE

| File | FY | Rows | Columns | Missing concepts | Bad FIPS | Bad HUD code | Duplicate FIPS | Null rents | Valid |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `FMR2024_final_revised.xlsx` | 2024 | 4,764 | 14 | None | 0 | 0 | 0 | 0 | TRUE |
| `FY18_4050_FMRs_rev.xlsx` | 2018 | 4,769 | 20 | None | 0 | 0 | 0 | 0 | TRUE |
| `FY2019_4050_FMRs_rev2.xlsx` | 2019 | 4,767 | 20 | None | 0 | 0 | 0 | 0 | TRUE |
| `FY20_4050_FMRs_rev.xlsx` | 2020 | 4,766 | 20 | None | 0 | 0 | 0 | 0 | TRUE |
| `FY21_4050_FMRs_rev.xlsx` | 2021 | 4,766 | 16 | None | 0 | 0 | 0 | 0 | TRUE |
| `FY22_FMRs_revised.xlsx` | 2022 | 4,765 | 14 | None | 0 | 0 | 0 | 0 | TRUE |
| `FY23_FMRs_revised.xlsx` | 2023 | 4,764 | 14 | None | 0 | 0 | 0 | 0 | TRUE |
| `FY25_FMRs_revised.xlsx` | 2025 | 4,764 | 14 | None | 0 | 0 | 0 | 0 | TRUE |
| `FY26_FMRs_revised.xlsx` | 2026 | 4,764 | 14 | None | 0 | 0 | 0 | 0 | TRUE |

## Schema Drift

Schema drift is expected across years and is handled by the Silver transformer through concept-level mappings.
- FY 2023: `fips, hud_area_name, hud_area_code, countyname, county_town_name, state, state_alpha, metro, pop2020, fmr_0, fmr_1, fmr_2, fmr_3, fmr_4`
- FY 2018: `fips2010, fmr_0, fmr_1, fmr_2, fmr_3, fmr_4, state, metro_code, areaname, county, cousub, countyname, county_town_name, pop2010, acs_2017_2, state_alpha, fmr_type, metro, fmr_pct_chg, fmr_dollar_chg`
- FY 2019: `fips2010, fmr_0, fmr_1, fmr_2, fmr_3, fmr_4, state, metro_code, areaname, county, cousub, countyname, county_town_name, pop2010, acs_2018_2, state_alpha, fmr_type, metro, fmr_pct_chg, fmr_dollar_chg`
- FY 2020: `fips2010, fmr_0, fmr_1, fmr_2, fmr_3, fmr_4, state, metro_code, areaname, county, cousub, countyname, county_town_name, pop2017, acs_2019_2, state_alpha, fmr_type, metro, fmr_pct_chg, fmr_dollar_chg`
- FY 2021: `fips2010, fmr_0, fmr_1, fmr_2, fmr_3, fmr_4, state, metro_code, areaname, county, cousub, countyname, county_town_name, pop2017, state_alpha, metro`
- FY 2022: `fips2010, fmr_0, fmr_1, fmr_2, fmr_3, fmr_4, state, metro_code, areaname, countyname, county_town_name, pop2017, state_alpha, metro`
- FY 2024: `stusps, state, hud_area_code, countyname, county_town_name, metro, hud_area_name, fips, pop2020, fmr_0, fmr_1, fmr_2, fmr_3, fmr_4`
- FY 2025: `stusps, state, hud_area_code, countyname, county_town_name, metro, hud_area_name, fips, pop2022, fmr_0, fmr_1, fmr_2, fmr_3, fmr_4`
- FY 2026: `stusps, state, hud_area_code, countyname, county_town_name, metro, hud_area_name, fips, pop2023, fmr_0, fmr_1, fmr_2, fmr_3, fmr_4`
