"""Neo4j configuration and connection management."""

from __future__ import annotations

import os

from neo4j import Driver, GraphDatabase


class Neo4jConfig:
    """Configuration for Neo4j connection."""

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize Neo4j configuration from arguments or environment variables.

        Args:
            uri: Neo4j connection URI (default: env NEO4J_URI)
            user: Neo4j username (default: env NEO4J_USER)
            password: Neo4j password (default: env NEO4J_PASSWORD)

        Raises:
            ValueError: If required configuration is missing.
        """
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USER")
        self.password = password or os.getenv("NEO4J_PASSWORD")

        if not self.uri:
            raise ValueError("NEO4J_URI must be provided via argument or environment variable")
        if not self.user:
            raise ValueError("NEO4J_USER must be provided via argument or environment variable")
        if not self.password:
            raise ValueError("NEO4J_PASSWORD must be provided via argument or environment variable")

    def get_driver(self) -> Driver:
        """Create and return a Neo4j driver.

        Returns:
            Neo4j Driver instance.

        Raises:
            Exception: If connection fails.
        """
        try:
            driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
            # Test the connection
            driver.verify_connectivity()
            return driver
        except Exception as e:
            raise Exception(f"Failed to connect to Neo4j at {self.uri}: {e}") from e

    @staticmethod
    def validate_env_vars() -> bool:
        """Validate that all required environment variables are set.

        Returns:
            True if all variables are set, False otherwise.
        """
        required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            print(f"Missing environment variables: {', '.join(missing)}")
            return False
        return True
