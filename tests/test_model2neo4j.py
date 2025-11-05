from langchain_text_splitters import RecursiveCharacterTextSplitter

from vapor.utils import model2neo4j


def test_generate_chunks():
    """Tests generating chunks for dummy game descriptions"""
    # Setup a default text splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=0)
    # Create some text
    game_doc = """
        This is a test game that is not real but has \n odd newlines. \n
    """
    # Generate chunks for test appid and verify
    appid = 1000
    chunks = model2neo4j.generate_game_description_chunks(
        appid, game_doc, text_splitter
    )
    for i, chunk in enumerate(chunks):
        assert chunk["text"]
        assert chunk["metadata"]
        assert chunk["metadata"]["chunk_id"] == f"{appid}-chunk{i}"
        assert chunk["metadata"]["source"] == appid
