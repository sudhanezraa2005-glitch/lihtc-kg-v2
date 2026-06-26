"""Loader for County IN_METRO_AREA MetroArea relationships."""

from typing import Any, LiteralString, cast

from neo4j import Driver

from .base_relationship_loader import BaseRelationshipLoader


class CountyMetroAreaRelationshipLoader(BaseRelationshipLoader):
    """Load (:County)-[:IN_METRO_AREA]->(:MetroArea) relationships."""

    source_label: LiteralString = "County"
    target_label: LiteralString = "MetroArea"
    relationship_type: LiteralString = "IN_METRO_AREA"
    source_match_key: LiteralString = "county_fips"
    source_join_key: LiteralString = "cbsa_number"
    target_match_key: LiteralString = "cbsa_code"
    target_business_key: LiteralString = "cbsa_code"

    def __init__(self, driver: Driver, batch_size: int = 10000) -> None:
        super().__init__(driver, batch_size)

    def _coverage_counts(self) -> tuple[int, int]:
        record = self._single_record_query(
            cast(
                LiteralString,
                """
                MATCH (m:MetroArea)
                WHERE m.cbsa_code IS NOT NULL

                OPTIONAL MATCH (c:County)
                WHERE toInteger(c.cbsa_number) = toInteger(m.cbsa_code)

                RETURN
                    count(m) AS eligible_source_count,
                    count(c) AS matched_target_count
                """,
            )
        )

        return (
            self._as_int(record["eligible_source_count"], "eligible_source_count"),
            self._as_int(record["matched_target_count"], "matched_target_count"),
        )

    def _fetch_batch(self, skip: int) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                cast(
                    LiteralString,
                    """
                    MATCH (m:MetroArea)
                    WHERE m.cbsa_code IS NOT NULL

                    WITH m
                    ORDER BY m.cbsa_code
                    SKIP $skip
                    LIMIT $limit

                    MATCH (c:County)
                    WHERE toInteger(c.cbsa_number) = toInteger(m.cbsa_code)

                    RETURN
                        c.county_fips AS source_id,
                        m.cbsa_code AS target_id
                    """,
                ),
                skip=skip,
                limit=self.batch_size,
            )

            return [dict(record) for record in result]