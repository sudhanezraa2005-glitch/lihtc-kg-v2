"""Loader for County HAS_CONFORMING_LIMIT ConformingLimitSnapshot relationships."""

from typing import LiteralString

from neo4j import Driver

from .base_relationship_loader import BaseRelationshipLoader


class ConformingLimitCountyRelationshipLoader(BaseRelationshipLoader):
    """Load (:County)-[:HAS_CONFORMING_LIMIT]->(:ConformingLimitSnapshot) relationships."""

    source_label: LiteralString = "County"
    target_label: LiteralString = "ConformingLimitSnapshot"
    relationship_type: LiteralString = "HAS_CONFORMING_LIMIT"
    source_match_key: LiteralString = "county_fips"
    source_join_key: LiteralString = "county_fips"
    target_match_key: LiteralString = "county_fips"
    target_business_key: LiteralString = "snapshot_id"

    def __init__(self, driver: Driver, batch_size: int = 10000) -> None:
        super().__init__(driver, batch_size)
