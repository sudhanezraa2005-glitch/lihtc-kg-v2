"""Loader for County CONTAINS CensusTract relationships."""

from typing import LiteralString

from neo4j import Driver

from .base_relationship_loader import BaseRelationshipLoader


class TractCountyRelationshipLoader(BaseRelationshipLoader):
    """Load (:County)-[:CONTAINS]->(:CensusTract) relationships."""

    source_label: LiteralString = "County"
    target_label: LiteralString = "CensusTract"
    relationship_type: LiteralString = "CONTAINS"
    source_match_key: LiteralString = "county_fips"
    source_join_key: LiteralString = "county_fips"
    target_match_key: LiteralString = "county_fips"
    target_business_key: LiteralString = "tract_fips"

    def __init__(self, driver: Driver, batch_size: int = 10000) -> None:
        super().__init__(driver, batch_size)
