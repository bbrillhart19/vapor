from contextlib import asynccontextmanager
from typing import AsyncIterator

from loguru import logger
from fastmcp import FastMCP

from vapor.core.db import driver
from vapor.core.models import embeddings
from . import tools


@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncIterator[None]:
    """Application lifespan manager - initializes and cleans up Neo4j driver."""
    # Initialize Neo4j driver
    logger.info("Initializing Neo4j driver...")
    driver._driver = driver.create_driver()
    logger.success("Neo4j driver initialized")

    # Initialize embedding model
    logger.info("Initializing embedding model...")
    embeddings._embedder = embeddings.VaporEmbeddings.from_env()
    embeddings._embedder.pull()
    logger.success("Embedding model initialized")

    try:
        yield
    finally:
        # Cleanup
        logger.info("Shutting down Neo4j driver...")
        driver._driver.close()
        logger.success("Cleanup complete")


def create_mcp_server() -> FastMCP:
    """Creates and configures the MCP server with all tools.

    Args:
        games_service: The games service instance for game-related operations.
        embedder: The embeddings model for semantic search.

    Returns:
        FastMCP: Configured MCP server instance with all tools registered.
    """
    mcp = FastMCP("Vapor MCP Server", lifespan=lifespan)

    # Register games tools
    tools.GamesTools(mcp)

    return mcp
