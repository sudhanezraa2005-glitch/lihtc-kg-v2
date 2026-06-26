"""Loader for State CONTAINS County relationships."""

from typing import LiteralString

from neo4j import Driver

from .base_relationship_loader import BaseRelationshipLoader


class CountyStateRelationshipLoader(BaseRelationshipLoader):
    """Load (:State)-[:CONTAINS]->(:County) relationships."""

    source_label: LiteralString = "State"
    target_label: LiteralString = "County"
    relationship_type: LiteralString = "CONTAINS"
    source_match_key: LiteralString = "state_fips"
    source_join_key: LiteralString = "state_fips"
    target_match_key: LiteralString = "state_fips"
    target_business_key: LiteralString = "county_fips"

    def __init__(self, driver: Driver, batch_size: int = 10000) -> None:
        super().__init__(driver, batch_size)
