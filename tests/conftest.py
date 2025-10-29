import random

import pytest
from pytest_mock import mocker

from vapor.utils import utils
from vapor.clients import Neo4jClient, SteamClient


@pytest.fixture(scope="function")
def steam_client() -> SteamClient:
    return SteamClient("test", "user0")


@pytest.fixture(scope="function")
def steam_users() -> dict[str, dict]:
    n_users = 10
    users = {}
    for i in range(n_users):
        steamid = f"user{i}"
        users[steamid] = {"personaname": f"user{i}", "steamid": steamid}
    return users


@pytest.fixture(scope="function")
def steam_friends(steam_users: dict[str, dict]) -> dict[str, list[dict]]:
    all_users = list(steam_users.keys())
    friends_lists = {}
    for steamid in steam_users:
        n_friends = random.randint(1, len(all_users))
        friends_lists[steamid] = [
            steam_users[u] for u in random.choices(all_users, k=n_friends)
        ]
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
        n_genres = random.randint(0, len(steam_genres))
        genres = random.choices(steam_genres, k=n_genres)
        games[appid] = {
            "appid": appid,
            "name": f"game{i}",
            "genres": genres,
        }
    return games


@pytest.fixture(scope="session")
def steam_owned_games(
    steam_users: dict[str, dict], steam_games: dict[int, dict]
) -> dict[str, list[dict]]:
    owned_games = {}
    all_games = list(steam_games.keys())
    for steamid in steam_users:
        n_owned_games = random.randint(0, len(all_games))
        playtime = random.randint(0, 1000)
        owned_games[steamid] = [
            {**steam_games[appid], "playtime_forever": playtime}
            for appid in random.choices(all_games, k=n_owned_games)
        ]
    return owned_games


@pytest.fixture(scope="function")
def neo4j_client() -> Neo4jClient:
    return Neo4jClient(
        uri="neo4j://localhost:7688",
        auth=("neo4j", "neo4j-dev"),
        database="neo4j",
    )
