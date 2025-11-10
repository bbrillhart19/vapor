from typing import Generator, Any

from rich.progress import track
from loguru import logger
from langchain_text_splitters import RecursiveCharacterTextSplitter

from vapor import models
from vapor.clients import Neo4jClient


def generate_game_description_chunks(
    appid: int,
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    **kwargs,
) -> Generator[dict[str, Any], None, None]:
    """Generate chunks of `text` representing the game description
    for `appid` with `RecursiveCharacterTextSplitter` from `langchain`.
    Each chunk will include the split text and metadata including a `chunk_id`.

    Args:
        appid (int): The identifier for the game.
        text (str): The game description to chunk.
        chunk_size (int, optional): The chunk size for the
            `text_splitter`. Defaults to 500.
        chunk_overlap (int, optional): The chunk overlap for
            the `text_splitter`. Defaults to 50.
        **kwargs: Additional keyword arguments to pass to the
            `text_splitter`. See `RecursiveCharacterTextSplitter`.

    Yields:
        dict[str, Any]: Each chunk with keys `"text"` and `"metadata"`.
    """
    # Setup text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
        **kwargs,
    )
    # Split the text into `Documents`
    chunks = text_splitter.create_documents([text])
    # Iterate splits and yield content along with metadata
    for i, chunk in enumerate(chunks):
        data = {
            "text": chunk.page_content,
            "chunkid": f"{appid}-chunk{i}",
            "source": appid,
            "start_index": chunk.metadata["start_index"],
            "total_length": len(chunk.page_content),
        }
        yield data


def embed_game_descriptions(neo4j_client: Neo4jClient, **kwargs) -> None:
    """Generate embeddings for chunks of text.

    Args:
        neo4j_client (Neo4jClient): The `Neo4jClient` for
            interaction with the Neo4j database.
        **kwargs: Keyword arguments to apply to the `text_splitter`.
    """

    # Retrieve all games and their descriptions
    all_games = neo4j_client.get_all_games().to_dict("records")
    game_descriptions_df = neo4j_client.get_game_descriptions(all_games)
    total_games = len(game_descriptions_df)
    logger.info(f"Found {total_games} total game descriptions to embed.")

    # Set embedding size
    embedding_size = models.EMBEDDER_PARAMS["embedding_size"]
    # Iterate over the descriptions, chunk, embed, and write
    for game in track(
        game_descriptions_df.itertuples(),
        description="Embedding:",
        total=total_games,
    ):
        # Extract chunks
        chunks: list[dict[str, Any]] = []
        texts: list[str] = []
        for chunk in generate_game_description_chunks(game.appid, game.about_the_game):
            texts.append(chunk.pop("text"))
            chunks.append(chunk)

        # Embed chunks
        embeddings = models.EMBEDDER.embed_documents(texts)
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]

        # Add to neo4j
        neo4j_client.set_game_description_embeddings(game.appid, chunks)

    # Set up vector index
    logger.info("Setting up game description chunks vector index...")
    neo4j_client.set_game_description_vector_index(embedding_dimension=embedding_size)
    logger.success("Set up game description embeddings successfully.")
