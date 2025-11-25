import json

import pytest
from langchain.tools import ToolRuntime
import pandas as pd

from vapor._types import VaporContext
from vapor.clients import Neo4jClient
from vapor import tools


@pytest.mark.neo4j
def test_about_the_game(tool_runtime: ToolRuntime[VaporContext]):
    """Tests the `about_the_game` tool for vapor agents"""
    appid = 1000
    search_name = "test game"
    actual_name = "Test Game II"
    description = "This is a test game description"
    tool_args = {"name": search_name, "runtime": tool_runtime}
    # Database should be clear - this should return empty
    result = tools.games.about_the_game.run(tool_args)
    assert result == json.dumps({})

    # Add a game with no description -> should return match but no description
    client = tool_runtime.context.neo4j_client
    cypher = """
        MERGE (g:Game {appId: $appid, name: $name})
    """
    client._write(cypher, appid=appid, name=actual_name)
    result = tools.games.about_the_game.run(tool_args)
    assert result == json.dumps({"matched_game": actual_name})

    # Add a description -> should return match and description
    cypher = """
        MATCH (g:Game {appId: $appid})
        SET g.aboutTheGame = $description
    """
    client._write(cypher, appid=appid, description=description)
    result = tools.games.about_the_game.run(tool_args)
    assert result == json.dumps(
        {"matched_game": actual_name, "about_the_game": description}
    )


def test_find_similar_games(mocker, tool_runtime: ToolRuntime[VaporContext]):
    """Tests `find_similar_games` (semantic search) tool for vapor agents"""
    query = "A test game"
    tool_args = {"summarized_description": query, "runtime": tool_runtime}
    # Test empty result
    mocker.patch.object(
        tool_runtime.context.neo4j_client,
        "game_descriptions_semantic_search",
        return_value=pd.DataFrame([{}]),
    )
    result = tools.games.find_similar_games.run(tool_args)
    assert result == ""

    # Mock the neo4j client function for return similar games
    mock_result = {"name": "Test", "appid": 1000, "desc": "A test game"}
    mocker.patch.object(
        tool_runtime.context.neo4j_client,
        "game_descriptions_semantic_search",
        return_value=pd.DataFrame([mock_result]),
    )
    result = tools.games.find_similar_games.run(tool_args)
    expected_result = [
        {
            "name": mock_result["name"],
            "appid": mock_result["appid"],
            "description_chunks": [mock_result["desc"]],
        }
    ]
    assert result == json.dumps(expected_result)
