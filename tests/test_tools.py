import json
import asyncio

import pytest
import pandas as pd
from fastmcp import FastMCP

from vapor.core.clients import Neo4jClient
from vapor.core.models.embeddings import VaporEmbeddings
from vapor.app import mcp


@pytest.mark.neo4j
async def test_about_the_game(
    mock_mcp: FastMCP, neo4j_client: Neo4jClient, mock_embedder: VaporEmbeddings
):
    """Tests the `about_the_game` tool for vapor agents"""
    game_tools = mcp.GamesTools(
        mcp_instance=mock_mcp,
        neo4j_client=neo4j_client,
        embedder=mock_embedder,
    )
    appid = 1000
    search_name = "test game"
    actual_name = "Test Game II"
    description = "This is a test game description"
    # Database should be clear - this should return empty
    result = await game_tools.about_the_game(search_name)
    assert result == {}

    # Add a game with no description -> should return match but no description
    cypher = """
        MERGE (g:Game {appId: $appid, name: $name})
    """
    neo4j_client._write(cypher, appid=appid, name=actual_name)
    result = await game_tools.about_the_game(search_name)
    assert result == {"matched_game": actual_name}

    # Add a description -> should return match and description
    cypher = """
        MATCH (g:Game {appId: $appid})
        SET g.aboutTheGame = $description
    """
    neo4j_client._write(cypher, appid=appid, description=description)
    result = await game_tools.about_the_game(search_name)
    assert result == {"matched_game": actual_name, "about_the_game": description}


@pytest.mark.neo4j
async def test_find_similar_games(
    mocker, mock_mcp: FastMCP, neo4j_client: Neo4jClient, mock_embedder: VaporEmbeddings
):
    """Tests `find_similar_games` (semantic search) tool for vapor agents"""
    game_tools = mcp.GamesTools(
        mcp_instance=mock_mcp,
        neo4j_client=neo4j_client,
        embedder=mock_embedder,
    )
    query = "A test game"
    # Test empty result
    mocker.patch.object(
        neo4j_client,
        "game_descriptions_semantic_search",
        return_value=pd.DataFrame([{}]),
    )
    result = await game_tools.find_similar_games(query)
    assert result == []

    # Mock the neo4j client function for return similar games
    mock_result = {"name": "Test", "appid": 1000, "desc": "A test game"}
    mocker.patch.object(
        neo4j_client,
        "game_descriptions_semantic_search",
        return_value=pd.DataFrame([mock_result]),
    )
    result = await game_tools.find_similar_games(query)
    expected_result = [
        {
            "name": mock_result["name"],
            "appid": mock_result["appid"],
            "description_chunks": [mock_result["desc"]],
        }
    ]
    assert result == expected_result
