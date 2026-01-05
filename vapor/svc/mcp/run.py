from loguru import logger
from fastmcp import FastMCP

from vapor.core.clients import Neo4jClient
from vapor.core.models.embeddings import VaporEmbeddings
from vapor.svc.mcp import GamesTools

logger.info("Initializing Vapor MCP Server >>>")
mcp = FastMCP("Vapor MCP Server")

logger.info("Setting up Neo4JClient...")
neo4j_client = Neo4jClient.from_env()
logger.info("Setting up Embedding Model...")
embedder = VaporEmbeddings.from_env()
embedder.pull()

logger.info("Setting up Games Tools...")
games = GamesTools(
    mcp_instance=mcp,
    neo4j_client=neo4j_client,
    embedder=embedder,
)

if __name__ == "__main__":
    mcp.run()
