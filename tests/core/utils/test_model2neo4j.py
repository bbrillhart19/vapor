import pytest

from vapor.core.models.embeddings import VaporEmbeddings
from vapor.core.utils import model2neo4j
from vapor.core.clients import Neo4jClient


def test_generate_chunks():
    """Tests generating chunks for dummy game descriptions"""
    # Create some text
    game_doc = """
        This is a test game that is not real but has \n odd newlines. \n
    """
    # Generate chunks for test appid and verify
    appid = 1000
    chunks = model2neo4j.generate_game_description_chunks(
        appid,
        game_doc,
        chunk_size=50,
        chunk_overlap=10,
    )
    for i, chunk in enumerate(chunks):
        assert chunk["text"]
        assert chunk["chunkid"] == f"{appid}-chunk{i}"
        assert chunk["source"] == appid
        assert isinstance(chunk["start_index"], int)
        assert chunk["total_length"] > 0


@pytest.mark.neo4j
def test_embed_game_descriptions(
    mock_embedder: VaporEmbeddings, neo4j_client: Neo4jClient
):
    """Tests creating embeddings from game descriptions
    and writing to neo4j database
    """
    # Create games w/ descriptions
    appid = 1000
    games = []
    for i in range(3):
        appid += i
        games.append(
            {"appid": appid, "desc": f"This is a game description for {appid}"}
        )
    cypher = """
        UNWIND $games as game
        MERGE (g:Game {appId: game.appid})
        SET g.aboutTheGame = game.desc
    """
    neo4j_client._write(cypher, games=games)

    # Run the embedding process w/ mocked embedder
    model2neo4j.embed_game_descriptions(
        embedder=mock_embedder,
        neo4j_client=neo4j_client,
    )

    # Check embeddings
    cypher = """
        MATCH (g:Game)-[:HAS_DESCRIPTION_CHUNK]->(c:DescriptionChunk)
        RETURN 
            g.appId as appid,
            c.chunkId as chunk_id,
            c.startIndex as start_index,
            c.source as source,
            c.totalLength as total_length,
            c.embedding as embedding
        """
    result = neo4j_client._read(cypher)
    for game in games:
        appid = game["appid"]
        rows = result.loc[result["appid"] == appid]
        assert not rows.empty
        for row in rows.itertuples():
            assert isinstance(row.start_index, int)
            assert row.chunk_id.startswith(str(row.appid))
            assert row.source == appid
            assert row.total_length > 0
            assert len(row.embedding) == mock_embedder.embedding_size
