import os

import pytest
import pandas as pd

from vapor.clients import Neo4jClient
from vapor.clients.neo4jclient import NotFoundException

from helpers import globals


def test_neo4j_from_env(mocker):
    """Tests setting up `SteamClient` from env vars"""
    mocker.patch.dict(
        os.environ,
        {
            "NEO4J_URI": globals.NEO4J_URI,
            "NEO4J_USER": globals.NEO4J_USER,
            "NEO4J_PW": globals.NEO4J_PW,
            "NEO4J_DATABASE": globals.NEO4J_DATABASE,
        },
    )
    client = Neo4jClient.from_env()


def test_io(neo4j_client: Neo4jClient):
    """Tests the `_write` and `_read` method(s) for the `Neo4jClient`"""
    cypher = """
        MERGE (n:Node {name: $name})
    """
    neo4j_client._write(cypher, name="test")
    cypher = """
        MATCH (n:Node {name: $name})
        RETURN n.name as name
    """
    result = neo4j_client._read(cypher, name="test", limit=1)
    assert isinstance(result, pd.DataFrame)
    assert result.iloc[0]["name"] == "test"

    # Clear the DB
    cypher = """
        MATCH (n)
        DETACH DELETE n
    """
    neo4j_client._write(cypher)
