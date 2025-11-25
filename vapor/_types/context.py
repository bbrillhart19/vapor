from dataclasses import dataclass

from vapor.clients import Neo4jClient
from vapor.models.embeddings import VaporEmbeddings


@dataclass
class VaporContext:
    """Defines the runtime context for Vapor agents"""

    neo4j_client: Neo4jClient
    embedder: VaporEmbeddings
