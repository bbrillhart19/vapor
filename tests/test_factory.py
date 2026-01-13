import pytest

from vapor.core.clients import Neo4jClient
from vapor.core.models.embeddings import VaporEmbeddings
from vapor.app.factory import create_app


@pytest.mark.neo4j
def test_create_app(mocker, neo4j_client: Neo4jClient, mock_embedder: VaporEmbeddings):
    """Tests the `create_app` start up process for Vapor application layer"""
    mocker.patch.object(Neo4jClient, "from_env", return_value=neo4j_client)
    mocker.patch.object(VaporEmbeddings, "pull", return_value=None)
    create_app()
