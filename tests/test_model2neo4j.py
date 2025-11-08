from langchain_ollama import OllamaEmbeddings

from vapor.utils import model2neo4j
from vapor.clients import Neo4jClient


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
        assert chunk["metadata"]
        assert chunk["metadata"]["chunk_id"] == f"{appid}-chunk{i}"
        assert chunk["metadata"]["source"] == appid


def test_embed_game_descriptions(mocker, neo4j_client: Neo4jClient):
    """Tests creating embeddings from game descriptions
    and writing to neo4j database
    """

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

    def mock_embed_docs(texts: list[str], *args, **kwargs) -> list[list[float]]:
        return [[0.5] * 20] * len(texts)

    mocker.patch.object(
        OllamaEmbeddings,
        "embed_documents",
        side_effect=mock_embed_docs,
    )

    model2neo4j.embed_game_descriptions(neo4j_client)
