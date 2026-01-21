"""MCP Server entry point - runs as a separate service"""

from vapor.mcp_server.factory import create_mcp_server

# Create the MCP server instance
mcp = create_mcp_server()
