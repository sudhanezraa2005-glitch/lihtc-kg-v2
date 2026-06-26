# ACS Completeness Report

## Enabled Coverage

- Years: 2009-2024 (16 years)
- States: 51 state FIPS codes
- Enabled tables: 12
- Enabled variables: 65

## Tables Requiring Special Handling

- `B17001`: Poverty table maps universe, below-poverty, and at/above-poverty totals. Additional age/sex detail can be added later by registry.
- `B25070`: Rent burden distribution table maps multiple percentage buckets; derived burden rates should be computed downstream or added explicitly.
- `B25031`: Median gross rent by bedroom count contains multiple median metrics; do not sum medians.
- `B03002`: Race/ethnicity table maps mutually related categories; derived percentages and rollups require explicit definitions.
- `B23025`: Employment table supports unemployment/labor force rates as derived metrics; current config stores counts only.

## Prepared But Not Enabled

- `B25024`: Units in Structure
- `B25034`: Year Structure Built
- `B25140`: Housing Costs by Tenure
- `B15003`: Educational Attainment
- `B25014`: Occupants per Room by Tenure
- `B25041`: Bedrooms

## Sentinel Handling

Silver transformation consistently converts `-666666666`, `-888888888`, and `-999999999` to null before parquet output.
