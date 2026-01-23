from contextlib import asynccontextmanager
from typing import AsyncIterator

from loguru import logger
from fastapi import FastAPI
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from vapor.app import routes, agent
from vapor.core.models.llm import VaporLLM
from vapor.core.models.prompts import load_prompt
from vapor.core.utils import utils


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager - initializes LLM agent with MCP tools."""
    # Initialize LLM
    logger.info("Initializing LLM...")
    llm = VaporLLM.from_env(temperature=0.7, num_ctx=4096)

    # Load chat prompt
    logger.info("Loading chat prompt...")
    prompt = load_prompt("chat")

    # Connect to MCP server (handle Docker vs local)
    # In Docker: use container name and internal port (8000)
    # Locally: use localhost and external mapped port from MCP_PORT
    if utils.in_docker():
        mcp_host = utils.get_env_var("MCP_DOCKER_HOST_NAME", "vapor-mcp")
        mcp_port = "8000"  # Internal container port
    else:
        mcp_host = "localhost"
        mcp_port = utils.get_env_var("MCP_PORT")
    mcp_url = f"http://{mcp_host}:{mcp_port}/mcp"
    logger.info(f"Connecting to MCP Server @ {mcp_url}...")

    agent._mcp_client = MultiServerMCPClient(
        {
            "vapor-mcp": {
                "transport": "http",
                "url": mcp_url,
            }
        }
    )

    # Get tools and create agent
    tools = await agent._mcp_client.get_tools()
    agent._agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt,
    )
    logger.success("Agent initialized successfully")

    try:
        yield
    finally:
        # Cleanup
        logger.info("Shutting down agent...")
        agent._agent = None
        agent._mcp_client = None
        logger.success("Cleanup complete")


@logger.catch
def create_app() -> FastAPI:
    """Creates the Vapor REST API application"""
    logger.info("Creating Vapor API...")
    app = FastAPI(title="Vapor API", lifespan=lifespan)

    # Add API Routers
    app.include_router(routes.status_router)
    app.include_router(routes.chat_router)

    return app
