# FHFA Graph Load Order

This document specifies the recommended graph load and relationship sequence for the FHFA Knowledge Graph.

## Node load order

1. `State`
2. `MetroArea`
3. `County`
4. `FMRSnapshot`
5. `CensusTract`
6. `HPISnapshot`
7. `ConformingLimitSnapshot`

## Relationship load order

1. `State` -[:CONTAINS]-> `County`
2. `County` -[:IN_METRO_AREA]-> `MetroArea`
3. `County` -[:CONTAINS]-> `CensusTract`
4. `CensusTract` -[:HAS_HPI]-> `HPISnapshot`
5. `County` -[:HAS_CONFORMING_LIMIT]-> `ConformingLimitSnapshot`
6. `County` -[:HAS_FMR]-> `FMRSnapshot`

## Notes

- Load stable geography nodes before snapshot nodes.
- Create State and MetroArea nodes first so dependent County and snapshot relationships can attach.
- Load `CensusTract` before `HPISnapshot` to ensure tract relationships exist.
- `ConformingLimitSnapshot` nodes can be created after `County` nodes are available.
- `FMRSnapshot` nodes join directly to `County` through `county_fips`.
