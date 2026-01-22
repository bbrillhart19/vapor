import random
from typing import Generator

import pytest
from fastmcp import FastMCP
from neo4j import Driver, GraphDatabase

from vapor.core.models import embeddings
from vapor.core.clients import Neo4jClient, SteamClient

from helpers import globals

random.seed(globals.SEED)


# ============================================================================
# Steam fixtures
# ============================================================================


@pytest.fixture(scope="function")
def steam_client() -> SteamClient:
    return SteamClient(globals.STEAM_API_KEY, globals.STEAM_ID)


@pytest.fixture(scope="function")
def steam_users() -> dict[str, dict]:
    n_users = 10
    users = {}
    for i in range(n_users):
        steamid = globals.STEAM_ID[:-4] + str(int(globals.STEAM_ID[-4:]) + i)
        users[steamid] = {"personaname": f"user{i}", "steamid": steamid}
    return users


@pytest.fixture(scope="function")
def steam_friends(steam_users: dict[str, dict]) -> dict[str, list[str]]:
    all_users = list(steam_users.keys())
    friends_lists = {steamid: [] for steamid in all_users}
    for steamid in steam_users:
        n_friends = random.randint(1, len(all_users))
        friends = random.sample(all_users, k=n_friends)
        for friend in friends:
            if friend not in friends_lists[steamid]:
                friends_lists[steamid].append(friend)
            if steamid not in friends_lists[friend]:
                friends_lists[friend].append(steamid)
    return friends_lists


@pytest.fixture(scope="function")
def steam_genres() -> list[dict]:
    n_genres = 10
    genres = [{"id": i, "description": f"genre{i}"} for i in range(n_genres)]
    return genres


@pytest.fixture(scope="function")
def steam_games(steam_genres: list[dict]) -> dict[int, dict]:
    n_games = 30
    games = {}
    for i in range(n_games):
        appid = 1000 + i
        n_genres = random.randint(1, len(steam_genres))
        genres = random.sample(steam_genres, k=n_genres)
        games[appid] = {
            "appid": appid,
            "name": f"game{i}",
            "genres": genres,
        }
    return games


@pytest.fixture(scope="function")
def steam_owned_games(
    steam_users: dict[str, dict], steam_games: dict[int, dict]
) -> dict[str, list[dict]]:
    owned_games = {}
    all_games = list(steam_games.keys())
    for steamid in steam_users:
        n_owned_games = random.randint(2, len(all_games))
        playtime = random.randint(0, 1000)
        playtime_2weeks = playtime / 2
        owned_games[steamid] = [
            {
                **steam_games[appid],
                "playtime_forever": playtime,
                "playtime_2weeks": playtime_2weeks,
            }
            for appid in random.sample(all_games, k=n_owned_games)
        ]
    return owned_games


# ============================================================================
# Neo4j fixtures
# ============================================================================


@pytest.fixture(scope="function")
def neo4j_driver() -> Generator[Driver, None, None]:
    """Provides a Neo4j driver instance for tests requiring database access.

    This fixture connects to the dev Neo4j instance and ensures the database
    is completely cleared after each test to prevent test artifacts from
    affecting subsequent tests.

    Yields:
        Driver: A Neo4j driver instance connected to the dev database.
    """
    driver = GraphDatabase.driver(
        uri=f"neo4j://localhost:{globals.NEO4J_BOLT_PORT}",
        auth=(globals.NEO4J_USER, globals.NEO4J_PW),
        database=globals.NEO4J_DATABASE,
    )
    yield driver
    # Clear the database after each test
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        # Also drop any indexes/constraints that may have been created
        session.run("CALL apoc.schema.assert({}, {})")
    driver.close()


@pytest.fixture(scope="function")
def neo4j_client() -> Generator[Neo4jClient, None, None]:
    """Provides a Neo4jClient instance for tests requiring the legacy client.

    This fixture is maintained for backward compatibility with existing tests
    that use the Neo4jClient directly.

    Yields:
        Neo4jClient: A client instance connected to the dev database.
    """
    client = Neo4jClient(
        uri=f"neo4j://localhost:{globals.NEO4J_BOLT_PORT}",
        auth=(globals.NEO4J_USER, globals.NEO4J_PW),
        database=globals.NEO4J_DATABASE,
    )
    yield client
    client.clear()


# ============================================================================
# Mock fixtures
# ============================================================================


@pytest.fixture(scope="function")
def mock_embedder(mocker):
    """Provides a mocked VaporEmbeddings instance.

    The embedder is mocked to return fixed-size vectors without
    actually calling the embedding model.

    Returns:
        VaporEmbeddings: A mocked embedder instance.
    """
    model = globals.OLLAMA_EMBEDDING_MODEL
    embedding_size = 10
    mocker.patch.dict(
        embeddings.EMBEDDING_PARAMS, {model: {"embedding_size": embedding_size}}
    )

    def mock_embed_docs(texts: list[str], *args, **kwargs) -> list[list[float]]:
        return [[0.5] * embedding_size] * len(texts)

    def mock_embed_query(text: str, *args, **kwargs) -> list[float]:
        return [0.5] * embedding_size

    mocker.patch.object(
        embeddings.VaporEmbeddings,
        "embed_documents",
        side_effect=mock_embed_docs,
    )
    mocker.patch.object(
        embeddings.VaporEmbeddings,
        "embed_query",
        side_effect=mock_embed_query,
    )

    return embeddings.VaporEmbeddings(model=model)


@pytest.fixture(scope="function")
def mock_mcp(mocker) -> FastMCP:
    """Provides a mocked FastMCP instance.

    Returns:
        FastMCP: A mocked MCP instance for testing tools.
    """
    mocker.patch.object(FastMCP, "__init__", return_value=None)
    mocker.patch.object(FastMCP, "tool", return_value=None)
    return FastMCP()
