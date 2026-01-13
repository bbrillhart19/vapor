from loguru import logger
from fastmcp import FastMCP
from fastapi import FastAPI

from vapor.core.clients import Neo4jClient
from vapor.core.models.embeddings import VaporEmbeddings
from vapor.app import mcp, routes


def create_app() -> FastAPI:
    """Creates the Vapor `FastAPI` application with mounted `FastMCP` server"""
    logger.info("Initializing Vapor services >>>")

    ### Setup dependencies ###
    logger.info("Setting up Neo4jClient...")
    neo4j_client = Neo4jClient.from_env()
    logger.info("Setting up Embedding Model...")
    embedder = VaporEmbeddings.from_env()
    embedder.pull()

    ### Setup MCP ###
    logger.info("Setting up MCP...")
    _mcp = FastMCP("Vapor MCP Server")
    games = mcp.GamesTools(
        mcp_instance=_mcp,
        neo4j_client=neo4j_client,
        embedder=embedder,
    )
    mcp_app = _mcp.http_app(path="/")

    ### Create API ###
    logger.info("Creating app...")
    # Create instance and mount mcp
    app = FastAPI(title="Vapor API", lifespan=mcp_app.lifespan)
    app.mount("/mcp", mcp_app)
    # Add routers
    app.include_router(routes.status_router)

    return app
