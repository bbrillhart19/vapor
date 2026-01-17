from contextlib import asynccontextmanager
from typing import AsyncIterator

from loguru import logger

# from fastmcp import FastMCP
from fastapi import FastAPI

# from vapor.core.clients import Neo4jClient
# from vapor.core.models.embeddings import VaporEmbeddings
from vapor.app import routes
from vapor.app.db import driver


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    driver._driver = driver.create_driver()
    try:
        yield
    finally:
        driver._driver.close()


@logger.catch
def create_app() -> FastAPI:
    """Creates the Vapor `FastAPI` application with mounted `FastMCP` server"""
    ### Create API ###
    logger.info("Creating Vapor API...")
    # Create instance and mount mcp
    app = FastAPI(title="Vapor API", lifespan=lifespan)
    # app.mount("/mcp", mcp_app)
    # Add routers
    app.include_router(routes.status_router)
    app.include_router(routes.games_router)

    return app
