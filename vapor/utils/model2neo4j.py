from typing import Generator, Any

from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from vapor.clients import Neo4jClient


def generate_game_description_chunks(
    appid: int, text: str, text_splitter: RecursiveCharacterTextSplitter
) -> Generator[dict[str, Any], None, None]:
    """Generate chunks of `text` representing the game description
    for `appid` with `RecursiveCharacterTextSplitter` from `langchain`.
    Each chunk will include the split text and metadata including a `chunk_id`.

    Args:
        appid (int): The identifier for the game.
        text (str): The game description to chunk.
        text_splitter (RecursiveCharacterTextSplitter):
            The `TextSplitter` instance to perform the chunking.

    Yields:
        dict[str, Any]: Each chunk with keys `"text"` and `"metadata"`.
    """
    # Split the text
    chunks = text_splitter.split_text(text)
    # Iterate splits and yield content along with metadata
    for i, chunk in enumerate(chunks):
        metadata = {
            "chunk_id": f"{appid}-chunk{i}",
            "source": appid,
            "total_length": len(chunk),
        }
        yield {"text": chunk, "metadata": metadata}
