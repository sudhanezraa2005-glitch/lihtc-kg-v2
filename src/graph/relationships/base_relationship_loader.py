"""Base loader for Neo4j relationship ingestion."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
import logging
from typing import Any, LiteralString, cast
from neo4j import Driver


@dataclass(frozen=True)
class RelationshipLoadStats:
    """Counts collected while validating or loading one relationship type."""

    relationship_type: str
    eligible_source_count: int
    matched_target_count: int
    relationships_created: int
    dry_run: bool


class BaseRelationshipLoader(ABC):
    """Base class for batched Neo4j relationship loaders."""

    source_label: LiteralString
    target_label: LiteralString
    relationship_type: LiteralString
    source_match_key: LiteralString
    source_join_key: LiteralString
    target_match_key: LiteralString
    target_business_key: LiteralString

    def __init__(self, driver: Driver, batch_size: int = 10000) -> None:
        """Initialize the base relationship loader.

        Args:
            driver: Neo4j driver instance.
            batch_size: Number of source nodes to inspect per batch.
        """
        self.driver = driver
        self.batch_size = batch_size
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_schema(self) -> None:
        """Validate that source and target nodes have the required join properties.

        Raises:
            ValueError: If source/target labels are empty or required join keys are absent.
        """
        source_stats = self._single_record_query(
            cast(
                LiteralString,
                f"""
                MATCH (s:{self.source_label})
                RETURN
                    count(s) AS node_count,
                    count(s.`{self.source_match_key}`) AS match_key_count,
                    count(s.`{self.source_join_key}`) AS join_key_count
                """,
            )
        )
        target_stats = self._single_record_query(
            cast(
                LiteralString,
                f"""
                MATCH (t:{self.target_label})
                RETURN
                    count(t) AS node_count,
                    count(t.`{self.target_match_key}`) AS match_key_count,
                    count(t.`{self.target_business_key}`) AS business_key_count
                """,
            )
        )

        source_count = self._as_int(source_stats["node_count"], "source node_count")
        source_match_count = self._as_int(source_stats["match_key_count"], "source match_key_count")
        source_join_count = self._as_int(source_stats["join_key_count"], "source join_key_count")
        target_count = self._as_int(target_stats["node_count"], "target node_count")
        target_match_count = self._as_int(target_stats["match_key_count"], "target match_key_count")
        target_business_count = self._as_int(
            target_stats["business_key_count"],
            "target business_key_count",
        )

        if source_count == 0:
            raise ValueError(f"No source nodes found for label {self.source_label}")
        if target_count == 0:
            raise ValueError(f"No target nodes found for label {self.target_label}")
        if source_match_count == 0:
            raise ValueError(
                f"No {self.source_label} nodes contain source match key {self.source_match_key}"
            )
        if source_join_count == 0:
            raise ValueError(
                f"No {self.source_label} nodes contain source join key {self.source_join_key}"
            )
        if target_match_count == 0:
            raise ValueError(
                f"No {self.target_label} nodes contain target match key {self.target_match_key}"
            )
        if target_business_count == 0:
            raise ValueError(
                f"No {self.target_label} nodes contain target business key {self.target_business_key}"
            )

    def dry_run(self) -> RelationshipLoadStats:
        """Validate and estimate relationship coverage without writing relationships."""
        self.validate_schema()
        eligible_source_count, matched_target_count = self._coverage_counts()
        self.logger.info(
            "Dry-run %s: %s eligible target nodes, %s matching source nodes",
            self.relationship_type,
            eligible_source_count,
            matched_target_count,
        )
        return RelationshipLoadStats(
            relationship_type=self.relationship_type,
            eligible_source_count=eligible_source_count,
            matched_target_count=matched_target_count,
            relationships_created=0,
            dry_run=True,
        )

    def load(self, dry_run: bool = False) -> RelationshipLoadStats:
        """Load relationships in batches.

        Args:
            dry_run: If True, validate and estimate coverage without writing.

        Returns:
            Relationship loading statistics.
        """
        if dry_run:
            return self.dry_run()

        self.validate_schema()
        eligible_source_count, matched_target_count = self._coverage_counts()
        self.logger.info(
            "Loading %s: %s eligible target nodes, %s resolvable relationships",
            self.relationship_type,
            eligible_source_count,
            matched_target_count,
        )

        relationships_created = 0
        processed_targets = 0
        skip = 0
        while skip < eligible_source_count:
            batch = self._fetch_batch(skip)
            if batch:
                created = self._execute_batch(batch)
                relationships_created += created
            processed_targets = min(skip + self.batch_size, eligible_source_count)
            self.logger.info(
                "Processed %s/%s target nodes for %s (%s relationships created so far)",
                processed_targets,
                eligible_source_count,
                self.relationship_type,
                relationships_created,
            )
            skip += self.batch_size

        return RelationshipLoadStats(
            relationship_type=self.relationship_type,
            eligible_source_count=eligible_source_count,
            matched_target_count=matched_target_count,
            relationships_created=relationships_created,
            dry_run=False,
        )

    def _coverage_counts(self) -> tuple[int, int]:
        record = self._single_record_query(
            cast(
                LiteralString,
                f"""
                MATCH (t:{self.target_label})
                WHERE t.`{self.target_business_key}` IS NOT NULL
                AND t.`{self.target_match_key}` IS NOT NULL

                OPTIONAL MATCH (s:{self.source_label})
                WHERE s.`{self.source_join_key}` = t.`{self.target_match_key}`

                RETURN
                    count(t) AS eligible_source_count,
                    count(s) AS matched_target_count
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
                    f"""
                    MATCH (t:{self.target_label})
                    WHERE t.`{self.target_business_key}` IS NOT NULL
                    AND t.`{self.target_match_key}` IS NOT NULL

                    WITH t
                    ORDER BY t.`{self.target_business_key}`
                    SKIP $skip
                    LIMIT $limit

                    MATCH (s:{self.source_label})
                    WHERE s.`{self.source_join_key}` = t.`{self.target_match_key}`

                    RETURN
                        s.`{self.source_match_key}` AS source_id,
                        t.`{self.target_business_key}` AS target_id
                    """,
                ),
                skip=skip,
                limit=self.batch_size,
            )

            return [dict(record) for record in result]

    def _execute_batch(self, batch: list[dict[str, Any]]) -> int:
        if not batch:
            return 0

        with self.driver.session() as session:
            result = session.run(
                cast(
                    LiteralString,
                    f"""
                    UNWIND $batch AS row
                    MATCH (s:{self.source_label} {{`{self.source_match_key}`: row.source_id}})
                    MATCH (t:{self.target_label} {{`{self.target_business_key}`: row.target_id}})
                    MERGE (s)-[:{self.relationship_type}]->(t)
                    """,
                ),
                batch=batch,
            )
            summary = result.consume()
            return summary.counters.relationships_created

    def _single_record_query(self, query: LiteralString) -> dict[str, Any]:
        with self.driver.session() as session:
            record = session.run(query).single()
            if record is None:
                return {}
            return dict(record)

    @staticmethod
    def _as_int(value: Any, field_name: str) -> int:
        if not isinstance(value, int):
            raise TypeError(f"Expected {field_name} to be int, got {type(value).__name__}")
        return value
