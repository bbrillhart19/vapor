from dataclasses import dataclass

from vapor.clients import Neo4jClient


@dataclass
class VaporContext:
    """Defines the runtime context for Vapor agents"""

    neo4j_client: Neo4jClient
