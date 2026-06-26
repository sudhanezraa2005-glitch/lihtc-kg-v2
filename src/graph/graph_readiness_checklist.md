# FHFA Graph Readiness Checklist

This checklist captures the validation and readiness items for the FHFA graph implementation.

## Ontology validation
- [ ] Confirm node labels match `metadata/ontology/fhfa_ontology.md`
- [ ] Verify property coverage for required stable nodes and snapshots
- [ ] Ensure business keys align with graph model and mapping spec

## Business key validation
- [ ] Validate uniqueness of `State.state_fips`
- [ ] Validate uniqueness of `County.county_fips`
- [ ] Validate uniqueness of `MetroArea.cbsa_code`
- [ ] Validate uniqueness of `CensusTract.tract_fips`
- [ ] Validate uniqueness of `HPISnapshot.snapshot_id`
- [ ] Validate uniqueness of `ConformingLimitSnapshot.snapshot_id`

## Duplicate validation
- [ ] Confirm the source datasets contain no duplicate business-key records
- [ ] Confirm `HPISnapshot` does not contain duplicate `(tract_fips, year)` pairs
- [ ] Confirm `ConformingLimitSnapshot` does not contain duplicate `(county_fips, year)` pairs

## Orphan validation
- [ ] Confirm every `CensusTract` maps to a `County`
- [ ] Confirm every `County` maps to a `State`
- [ ] Confirm every `HPISnapshot` maps to a `CensusTract`
- [ ] Confirm every `ConformingLimitSnapshot` maps to a `County`
- [ ] Confirm every non-null `County.cbsa_number` maps to a `MetroArea`

## Relationship coverage validation
- [ ] Verify `State` → `County` cardinality
- [ ] Verify `County` → `MetroArea` cardinality
- [ ] Verify `County` → `CensusTract` cardinality
- [ ] Verify `CensusTract` → `HPISnapshot` cardinality
- [ ] Verify `County` → `ConformingLimitSnapshot` cardinality

## Deployment readiness
- [ ] Confirm constraints and indexes are defined in `src/graph/constraints.cypher` and `src/graph/indexes.cypher`
- [ ] Confirm load order is documented in `src/graph/load_order.md`
- [ ] Confirm implementation plan is available in `metadata/graph/graph_implementation_plan.md`
