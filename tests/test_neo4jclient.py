import os

import pytest

from vapor.clients import Neo4jClient
from vapor.clients.neo4jclient import NotFoundException


def test_get_primary_user(neo4j_client: Neo4jClient) -> None:
    # Test correct retrieval
    result = neo4j_client.get_primary_user()
    assert result["steamid"] == os.environ["STEAM_ID"]
    assert result["personaname"]

    # Remove primary user to test not found, then add it back
    cypher = """
        MATCH (p:Primary)
        REMOVE p:Primary
    """
    neo4j_client._write(cypher)
    with pytest.raises(NotFoundException):
        neo4j_client.get_primary_user()

    cypher = """
        MATCH (u:User {steamId: $steamid})
        SET u:Primary
    """
    neo4j_client._write(cypher, steamid=result["steamid"])


def test_setup(neo4j_client: Neo4jClient) -> None:
    neo4j_client.is_setup
