from loguru import logger
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

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


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Basic health check that the server is running."""
    return JSONResponse({"status": "alive"}, status_code=200)


if __name__ == "__main__":
    mcp.run()
