import json

import pytest
from langchain.tools import ToolRuntime

from vapor._types import VaporContext
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
