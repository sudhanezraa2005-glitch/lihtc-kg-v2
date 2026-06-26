"""Read-only Neo4j graph validation for the FHFA knowledge graph."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from pathlib import Path
import sys
from typing import Any, Literal, LiteralString, cast

from neo4j import Driver

from src.graph.config.neo4j_config import Neo4jConfig


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RelationshipValidationSpec:
    """Relationship coverage and duplicate validation settings."""

    name: str
    source_label: LiteralString
    target_label: LiteralString
    relationship_type: LiteralString
    source_business_key: LiteralString
    source_join_key: LiteralString
    target_business_key: LiteralString
    target_join_key: LiteralString
    coverage_side: Literal["source", "target"]
    required: bool = True


@dataclass(frozen=True)
class NodeValidationSpec:
    """Node duplicate validation settings."""

    label: LiteralString
    business_key: LiteralString


@dataclass(frozen=True)
class RelationshipValidationResult:
    """Coverage and duplicate relationship counts for one relationship."""

    name: str
    eligible_source_count: int
    related_source_count: int
    missing_relationship_count: int
    duplicate_relationship_count: int
    semantic_mismatch_count: int
    coverage_percent: float
    required: bool


@dataclass(frozen=True)
class NodeDuplicateResult:
    """Duplicate node count for one business key."""

    label: str
    business_key: str
    duplicate_key_count: int
    duplicate_node_count: int


@dataclass(frozen=True)
class GraphValidationReport:
    """Full graph validation result."""

    generated_at: datetime
    relationship_results: list[RelationshipValidationResult]
    node_duplicate_results: list[NodeDuplicateResult]
    ready_for_full_load: bool


NODE_SPECS: list[NodeValidationSpec] = [
    NodeValidationSpec("State", "state_fips"),
    NodeValidationSpec("MetroArea", "cbsa_code"),
    NodeValidationSpec("County", "county_fips"),
    NodeValidationSpec("CensusTract", "tract_fips"),
    NodeValidationSpec("HPISnapshot", "snapshot_id"),
    NodeValidationSpec("ConformingLimitSnapshot", "snapshot_id"),
    NodeValidationSpec("FMRSnapshot", "snapshot_id"),
]


RELATIONSHIP_SPECS: list[RelationshipValidationSpec] = [
    RelationshipValidationSpec(
        name="State -> County",
        source_label="State",
        target_label="County",
        relationship_type="CONTAINS",
        source_business_key="state_fips",
        source_join_key="state_fips",
        target_business_key="county_fips",
        target_join_key="state_fips",
        coverage_side="target",
    ),
    RelationshipValidationSpec(
        name="County -> CensusTract",
        source_label="County",
        target_label="CensusTract",
        relationship_type="CONTAINS",
        source_business_key="county_fips",
        source_join_key="county_fips",
        target_business_key="tract_fips",
        target_join_key="county_fips",
        coverage_side="target",
    ),
    RelationshipValidationSpec(
        name="CensusTract -> HPISnapshot",
        source_label="CensusTract",
        target_label="HPISnapshot",
        relationship_type="HAS_HPI",
        source_business_key="tract_fips",
        source_join_key="tract_fips",
        target_business_key="snapshot_id",
        target_join_key="tract_fips",
        coverage_side="target",
    ),
    RelationshipValidationSpec(
        name="County -> ConformingLimitSnapshot",
        source_label="County",
        target_label="ConformingLimitSnapshot",
        relationship_type="HAS_CONFORMING_LIMIT",
        source_business_key="county_fips",
        source_join_key="county_fips",
        target_business_key="snapshot_id",
        target_join_key="county_fips",
        coverage_side="target",
    ),
    RelationshipValidationSpec(
        name="County -> FMRSnapshot",
        source_label="County",
        target_label="FMRSnapshot",
        relationship_type="HAS_FMR",
        source_business_key="county_fips",
        source_join_key="county_fips",
        target_business_key="snapshot_id",
        target_join_key="county_fips",
        coverage_side="target",
    ),
    RelationshipValidationSpec(
        name="County -> MetroArea",
        source_label="County",
        target_label="MetroArea",
        relationship_type="IN_METRO_AREA",
        source_business_key="county_fips",
        source_join_key="cbsa_number",
        target_business_key="cbsa_code",
        target_join_key="cbsa_code",
        coverage_side="source",
    ),
]


class GraphValidator:
    """Run read-only validation queries against a Neo4j graph."""

    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    def validate(self) -> GraphValidationReport:
        """Run all node and relationship validation checks."""
        node_duplicate_results = [self._validate_node_duplicates(spec) for spec in NODE_SPECS]
        relationship_results = [
            self._validate_relationship_coverage(spec) for spec in RELATIONSHIP_SPECS
        ]
        ready_for_full_load = self._is_ready(node_duplicate_results, relationship_results)

        return GraphValidationReport(
            generated_at=datetime.now(UTC),
            relationship_results=relationship_results,
            node_duplicate_results=node_duplicate_results,
            ready_for_full_load=ready_for_full_load,
        )

    def _validate_node_duplicates(self, spec: NodeValidationSpec) -> NodeDuplicateResult:
        logger.info("Checking duplicate %s nodes by %s", spec.label, spec.business_key)
        record = self._single_record_query(
            cast(
                LiteralString,
                f"""
                MATCH (n:{spec.label})
                WHERE n.`{spec.business_key}` IS NOT NULL
                WITH n.`{spec.business_key}` AS business_key, count(n) AS node_count
                WHERE node_count > 1
                RETURN
                    count(business_key) AS duplicate_key_count,
                    coalesce(sum(node_count), 0) AS duplicate_node_count
                """,
            )
        )
        return NodeDuplicateResult(
            label=spec.label,
            business_key=spec.business_key,
            duplicate_key_count=self._as_int(record["duplicate_key_count"], "duplicate_key_count"),
            duplicate_node_count=self._as_int(record["duplicate_node_count"], "duplicate_node_count"),
        )

    def _validate_relationship_coverage(
        self,
        spec: RelationshipValidationSpec,
    ) -> RelationshipValidationResult:
        logger.info("Checking relationship coverage for %s", spec.name)
        coverage_record = self._coverage_record(spec)
        join_condition = self._join_condition(spec)
        duplicate_record = self._single_record_query(
            cast(
                LiteralString,
                f"""
                MATCH (s:{spec.source_label})-[r:{spec.relationship_type}]->(t:{spec.target_label})
                WHERE s.`{spec.source_business_key}` IS NOT NULL
                  AND t.`{spec.target_business_key}` IS NOT NULL
                WITH
                    s.`{spec.source_business_key}` AS source_key,
                    t.`{spec.target_business_key}` AS target_key,
                    count(r) AS relationship_count
                WHERE relationship_count > 1
                RETURN coalesce(sum(relationship_count - 1), 0) AS duplicate_relationship_count
                """,
            )
        )
        semantic_record = self._single_record_query(
            cast(
                LiteralString,
                f"""
                MATCH (s:{spec.source_label})-[r:{spec.relationship_type}]->(t:{spec.target_label})
                WHERE s.`{spec.source_join_key}` IS NOT NULL
                  AND t.`{spec.target_join_key}` IS NOT NULL
                  AND NOT ({join_condition})
                RETURN count(r) AS semantic_mismatch_count
                """,
            )
        )

        eligible_source_count = self._as_int(
            coverage_record["eligible_source_count"],
            "eligible_source_count",
        )
        related_source_count = self._as_int(
            coverage_record["related_source_count"],
            "related_source_count",
        )
        missing_relationship_count = self._as_int(
            coverage_record["missing_relationship_count"],
            "missing_relationship_count",
        )
        duplicate_relationship_count = self._as_int(
            duplicate_record["duplicate_relationship_count"],
            "duplicate_relationship_count",
        )
        semantic_mismatch_count = self._as_int(
            semantic_record["semantic_mismatch_count"],
            "semantic_mismatch_count",
        )
        coverage_percent = (
            100.0 if eligible_source_count == 0 else related_source_count / eligible_source_count * 100
        )

        return RelationshipValidationResult(
            name=spec.name,
            eligible_source_count=eligible_source_count,
            related_source_count=related_source_count,
            missing_relationship_count=missing_relationship_count,
            duplicate_relationship_count=duplicate_relationship_count,
            semantic_mismatch_count=semantic_mismatch_count,
            coverage_percent=coverage_percent,
            required=spec.required,
        )

    @staticmethod
    def _is_ready(
        node_duplicate_results: list[NodeDuplicateResult],
        relationship_results: list[RelationshipValidationResult],
    ) -> bool:
        has_duplicate_nodes = any(
            result.duplicate_key_count > 0 or result.duplicate_node_count > 0
            for result in node_duplicate_results
        )
        has_relationship_issues = any(
            result.required
            and (
                result.missing_relationship_count > 0
                or result.duplicate_relationship_count > 0
                or result.semantic_mismatch_count > 0
                or result.coverage_percent < 100.0
            )
            for result in relationship_results
        )
        return not has_duplicate_nodes and not has_relationship_issues

    def _coverage_record(self, spec: RelationshipValidationSpec) -> dict[str, Any]:
        if spec.coverage_side == "source":
            return self._single_record_query(
                cast(
                    LiteralString,
                    f"""
                    MATCH (s:{spec.source_label})
                    WHERE s.`{spec.source_business_key}` IS NOT NULL
                      AND s.`{spec.source_join_key}` IS NOT NULL
                    OPTIONAL MATCH (s)-[r:{spec.relationship_type}]->(t:{spec.target_label})
                    WHERE {self._join_condition(spec)}
                    WITH s, count(r) AS relationship_count
                    RETURN
                        count(s) AS eligible_source_count,
                        sum(CASE WHEN relationship_count > 0 THEN 1 ELSE 0 END) AS related_source_count,
                        sum(CASE WHEN relationship_count = 0 THEN 1 ELSE 0 END) AS missing_relationship_count
                    """,
                )
            )

        return self._single_record_query(
            cast(
                LiteralString,
                f"""
                MATCH (t:{spec.target_label})
                WHERE t.`{spec.target_business_key}` IS NOT NULL
                  AND t.`{spec.target_join_key}` IS NOT NULL
                OPTIONAL MATCH (s:{spec.source_label})-[r:{spec.relationship_type}]->(t)
                WHERE {self._join_condition(spec)}
                WITH t, count(r) AS relationship_count
                RETURN
                    count(t) AS eligible_source_count,
                    sum(CASE WHEN relationship_count > 0 THEN 1 ELSE 0 END) AS related_source_count,
                    sum(CASE WHEN relationship_count = 0 THEN 1 ELSE 0 END) AS missing_relationship_count
                """,
            )
        )

    def _join_condition(self, spec: RelationshipValidationSpec) -> str:
        if spec.name == "State -> County":
            return "toInteger(s.`state_fips`) = toInteger(t.`state_fips`)"
        if spec.name == "County -> MetroArea":
            return "toInteger(s.`cbsa_number`) = toInteger(t.`cbsa_code`)"
        return f"s.`{spec.source_join_key}` = t.`{spec.target_join_key}`"

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


def render_markdown_report(report: GraphValidationReport) -> str:
    """Render validation results as Markdown."""
    ready_value = "TRUE" if report.ready_for_full_load else "FALSE"
    lines = [
        "# FHFA Knowledge Graph Validation Report",
        "",
        f"- Generated at: `{report.generated_at.isoformat()}`",
        f"- READY_FOR_FULL_LOAD = {ready_value}",
        "",
        "## Relationship Coverage Statistics",
        "",
        "| Check | Eligible sources | Related sources | Missing relationships | Duplicate relationships | Semantic mismatches | Coverage |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for result in report.relationship_results:
        lines.append(
            "| "
            f"{result.name} | "
            f"{result.eligible_source_count:,} | "
            f"{result.related_source_count:,} | "
            f"{result.missing_relationship_count:,} | "
            f"{result.duplicate_relationship_count:,} | "
            f"{result.semantic_mismatch_count:,} | "
            f"{result.coverage_percent:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Duplicate Nodes By Business Key",
            "",
            "| Label | Business key | Duplicate keys | Duplicate nodes |",
            "| --- | --- | ---: | ---: |",
        ]
    )

    for result in report.node_duplicate_results:
        lines.append(
            "| "
            f"{result.label} | "
            f"`{result.business_key}` | "
            f"{result.duplicate_key_count:,} | "
            f"{result.duplicate_node_count:,} |"
        )

    lines.extend(
        [
            "",
            "## Readiness Criteria",
            "",
            "- Orphan Counties: zero `County` nodes missing incoming `CONTAINS` from State.",
            "- Orphan CensusTracts: zero `CensusTract` nodes missing incoming `CONTAINS` from County.",
            "- Orphan HPISnapshots: zero `HPISnapshot` nodes missing incoming `HAS_HPI` from CensusTract.",
            "- Orphan ConformingLimitSnapshots: zero `ConformingLimitSnapshot` nodes missing incoming `HAS_CONFORMING_LIMIT` from County.",
            "- Orphan FMRSnapshots: zero `FMRSnapshot` nodes missing incoming `HAS_FMR` from County.",
            "- Missing Metro relationships: zero eligible `County` nodes missing `IN_METRO_AREA` MetroArea.",
            "- Duplicate nodes by business key: zero duplicate keys and duplicate nodes.",
            "- Duplicate relationships: zero duplicate relationships per source-target pair.",
            "- Semantic relationship mismatches: zero relationships where source and target join keys differ.",
            "- Relationship coverage: 100.00% for every required relationship check.",
            "",
            f"READY_FOR_FULL_LOAD = {ready_value}",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_graph(
    neo4j_uri: str | None = None,
    neo4j_user: str | None = None,
    neo4j_password: str | None = None,
) -> GraphValidationReport:
    """Validate the current Neo4j graph and return structured results."""
    if not Neo4jConfig.validate_env_vars() and not all([neo4j_uri, neo4j_user, neo4j_password]):
        raise ValueError(
            "Must provide Neo4j credentials via environment variables "
            "(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) or function arguments"
        )

    config = Neo4jConfig(neo4j_uri, neo4j_user, neo4j_password)
    driver = config.get_driver()
    logger.info("Connected to Neo4j at %s", config.uri)
    try:
        return GraphValidator(driver).validate()
    finally:
        driver.close()
        logger.info("Neo4j connection closed")


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Validate the FHFA Neo4j graph")
    parser.add_argument("--uri", help="Neo4j URI (default: env NEO4J_URI)")
    parser.add_argument("--user", help="Neo4j username (default: env NEO4J_USER)")
    parser.add_argument("--password", help="Neo4j password (default: env NEO4J_PASSWORD)")
    parser.add_argument("--output", help="Optional Markdown report output path")
    args = parser.parse_args()

    try:
        report = validate_graph(
            neo4j_uri=args.uri,
            neo4j_user=args.user,
            neo4j_password=args.password,
        )
        markdown = render_markdown_report(report)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            logger.info("Wrote validation report to %s", output_path)
        print(markdown)
        return 0 if report.ready_for_full_load else 1
    except Exception as exc:
        logger.error("Graph validation failed: %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
