"""Loader for CensusTract HAS_ACS ACSSnapshot relationships."""

from typing import LiteralString

from neo4j import Driver

from .base_relationship_loader import BaseRelationshipLoader


class ACSTractRelationshipLoader(BaseRelationshipLoader):
    """Load (:CensusTract)-[:HAS_ACS]->(:ACSSnapshot) relationships."""

    source_label: LiteralString = "CensusTract"

    target_label: LiteralString = "ACSSnapshot"

    relationship_type: LiteralString = "HAS_ACS"

    source_match_key: LiteralString = "tract_fips"

    source_join_key: LiteralString = "tract_fips"

    target_match_key: LiteralString = "tract_fips"

    target_business_key: LiteralString = "snapshot_id"

    def __init__(
        self,
        driver: Driver,
        batch_size: int = 10000,
    ) -> None:
        super().__init__(driver, batch_size)