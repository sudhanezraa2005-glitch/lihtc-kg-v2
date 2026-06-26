"""Loader for CensusTract HAS_HPI HPISnapshot relationships."""

from typing import LiteralString

from neo4j import Driver

from .base_relationship_loader import BaseRelationshipLoader


class HPITractRelationshipLoader(BaseRelationshipLoader):
    """Load (:CensusTract)-[:HAS_HPI]->(:HPISnapshot) relationships."""

    source_label: LiteralString = "CensusTract"
    target_label: LiteralString = "HPISnapshot"
    relationship_type: LiteralString = "HAS_HPI"
    source_match_key: LiteralString = "tract_fips"
    source_join_key: LiteralString = "tract_fips"
    target_match_key: LiteralString = "tract_fips"
    target_business_key: LiteralString = "snapshot_id"

    def __init__(self, driver: Driver, batch_size: int = 10000) -> None:
        super().__init__(driver, batch_size)
