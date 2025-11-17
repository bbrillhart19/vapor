import random
from typing import Generator

import pytest
from langchain.tools import ToolRuntime

from vapor._types import VaporContext
from vapor.clients import Neo4jClient, SteamClient

from helpers import globals


random.seed(globals.SEED)


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


@pytest.fixture(scope="function")
def neo4j_client() -> Generator[Neo4jClient, None, None]:
    client = Neo4jClient(
        uri=globals.NEO4J_URI,
        auth=(globals.NEO4J_USER, globals.NEO4J_PW),
        database=globals.NEO4J_DATABASE,
    )
    yield client
    client.clear()


@pytest.fixture(scope="function")
def vapor_ctx(neo4j_client: Neo4jClient) -> VaporContext:
    return VaporContext(neo4j_client=neo4j_client)


@pytest.fixture(scope="function")
def tool_runtime(vapor_ctx: VaporContext) -> ToolRuntime[VaporContext]:
    return ToolRuntime(
        context=vapor_ctx,
        config={},
        stream_writer=lambda x: None,
        state={"messages": []},
        store=None,
        tool_call_id="test_call_id",
    )
