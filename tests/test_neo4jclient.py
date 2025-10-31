import os

import pytest
import pandas as pd

from vapor.clients import Neo4jClient
from vapor.clients.neo4jclient import NotFoundException

from helpers import globals


def test_neo4j_from_env(mocker):
    """Tests setting up `SteamClient` from env vars"""
    mocker.patch.dict(
        os.environ,
        {
            "NEO4J_URI": globals.NEO4J_URI,
            "NEO4J_USER": globals.NEO4J_USER,
            "NEO4J_PW": globals.NEO4J_PW,
            "NEO4J_DATABASE": globals.NEO4J_DATABASE,
        },
    )
    client = Neo4jClient.from_env()


def test_io(neo4j_client: Neo4jClient):
    """Tests the `_write` and `_read` method(s) for the `Neo4jClient`"""
    cypher = """
        MERGE (n:Node {name: $name})
    """
    neo4j_client._write(cypher, name="test")
    cypher = """
        MATCH (n:Node {name: $name})
        RETURN n.name as name
    """
    result = neo4j_client._read(cypher, name="test", limit=1)
    assert isinstance(result, pd.DataFrame)
    assert result.iloc[0]["name"] == "test"


def test_setup(neo4j_client: Neo4jClient):
    """Tests the setup process"""
    # No primary user yet, so this should be False
    assert not neo4j_client.is_setup

    # Set the primary user
    neo4j_client.add_user(steamid=globals.STEAM_ID, personaname="user0")
    neo4j_client._set_primary_user(globals.STEAM_ID)
    # Attempt setup again, should return False with no constraints set
    assert not neo4j_client.is_setup

    # Clear the DB, and run full setup
    neo4j_client.clear()
    neo4j_client.setup_from_primary_user(steamid=globals.STEAM_ID, personaname="user0")
    # Check setup success
    assert neo4j_client.is_setup


def test_validate_node_fields(neo4j_client: Neo4jClient):
    """Tests the `_validate_node_fields` helper method"""
    # Set up some dummy nodes with missing info
    nodes = [
        # Valid node, will keep all pairs
        {"name": "n1", "foo": "bar"},
        # Invalid node missing required field, should skip
        {"foo": "bar"},
        # Valid node, missing optional field, will fill with default
        {"name": "n2"},
    ]
    # Set the defaults to validate with
    defaults = {"name": None, "foo": "baz"}
    # Run validation and verify
    validated_nodes = neo4j_client._validate_node_fields(nodes, defaults)
    expected = [{"name": "n1", "foo": "bar"}, {"name": "n2", "foo": "baz"}]
    assert validated_nodes == expected


def test_add_user(neo4j_client: Neo4jClient):
    """Tests the `add_user` method"""
    # Add a user
    neo4j_client.add_user(steamid=globals.STEAM_ID, personaname="user0")
    # Check it exists
    cypher = """
        MATCH (u:User)
        WHERE u.steamId = $steamid
        RETURN u.steamId as steamid, u.personaName as personaname
    """
    result = neo4j_client._read(cypher, steamid=globals.STEAM_ID)
    assert len(result) == 1
    assert result.iloc[0]["steamid"] == globals.STEAM_ID
    assert result.iloc[0]["personaname"] == "user0"


def test_get_all_users(neo4j_client: Neo4jClient, steam_users: dict[str, dict]):
    """Tests `get_all_users` retrieval method"""
    # Add the steam users
    users = list(steam_users.values())
    for user in users:
        neo4j_client.add_user(**user)
    # Retrieve users and verify
    result = neo4j_client.get_all_users()
    assert len(result) == len(users)
    for expected_user in users:
        assert not result.loc[
            (result["steamid"] == expected_user["steamid"])
            & (result["personaname"] == expected_user["personaname"])
        ].empty


def test_add_friends(neo4j_client: Neo4jClient, steam_friends: dict[str, list[dict]]):
    """Tests the `add_friends` method for a single user"""
    # Add user and their friends
    user_friends = steam_friends[globals.STEAM_ID]
    neo4j_client.add_user(steamid=globals.STEAM_ID, personaname="user0")
    neo4j_client.add_friends(steamid=globals.STEAM_ID, friends=user_friends)
    # Check the friendship relationships exist
    cypher = """
        MATCH (u:User {steamId: $steamid})-[:HAS_FRIEND]->(f:User)
        RETURN f.steamId as steamid, f.personaName as personaname
    """
    result = neo4j_client._read(cypher, steamid=globals.STEAM_ID)
    print(result.head())
    assert len(result) == len(user_friends)
    for expected_friend in user_friends:
        assert not result.loc[
            (result["steamid"] == expected_friend["steamid"])
            & (result["personaname"] == expected_friend["personaname"])
        ].empty


def test_owned_games(
    neo4j_client: Neo4jClient, steam_owned_games: dict[str, list[dict]]
):
    """Test `add_owned_games` and subsequently `get_owned_games`"""
    # Add user and their games
    user_owned_games = steam_owned_games[globals.STEAM_ID]
    neo4j_client.add_user(steamid=globals.STEAM_ID, personaname="user0")
    neo4j_client.add_owned_games(steamid=globals.STEAM_ID, games=user_owned_games)
    # Retrieve the owned games and verify
    result = neo4j_client.get_owned_games(steamid=globals.STEAM_ID)
    assert len(result) == len(user_owned_games)
    for expected_game in user_owned_games:
        assert not result.loc[
            (result["appid"] == expected_game["appid"])
            & (result["name"] == expected_game["name"])
        ].empty


def test_get_all_games(neo4j_client: Neo4jClient, steam_games: dict[int, dict]):
    """Tests retrieving all games with `get_all_games` method"""
    # Add all the games
    games = list(steam_games.values())
    cypher = """
        UNWIND $games as game
        MERGE (g:Game {appId: game.appid, name: game.name})
    """
    neo4j_client._write(cypher, games=games)
    # Read all and verify existence
    result = neo4j_client.get_all_games()
    assert len(result) == len(games)
    for expected_game in games:
        assert not result.loc[
            (result["appid"] == expected_game["appid"])
            & (result["name"] == expected_game["name"])
        ].empty


def test_add_game_genres(neo4j_client: Neo4jClient, steam_games: dict[int, dict]):
    """Tests add genres for all games with `add_game_genres` method"""
    # Add a game
    game = steam_games[1000]
    cypher = """
        MERGE (g:Game {appId: $appid, name: $name})
    """
    neo4j_client._write(cypher, appid=game["appid"], name=game["name"])
    # Add genres
    neo4j_client.add_game_genres(appid=game["appid"], genres=game["genres"])
    # Read genres and verify existence
    cypher = """
        MATCH (g:Game)-[:HAS_GENRE]->(n:Genre)
        RETURN n.genreId as id, n.description as description
    """
    result = neo4j_client._read(cypher)
    assert len(result) == len(game["genres"])
    for expected_genre in game["genres"]:
        assert not result.loc[
            (result["id"] == expected_genre["id"])
            & (result["description"] == expected_genre["description"])
        ].empty


def test_update_recently_played_games(
    neo4j_client: Neo4jClient, steam_owned_games: dict[str, list[dict]]
):
    """Test setting recently played games with `update_recently_played_games`"""
    # Add user and their games as recently played
    user_owned_games = steam_owned_games[globals.STEAM_ID]
    neo4j_client.add_user(steamid=globals.STEAM_ID, personaname="user0")
    neo4j_client.add_owned_games(steamid=globals.STEAM_ID, games=user_owned_games)
    neo4j_client.update_recently_played_games(
        steamid=globals.STEAM_ID, games=user_owned_games
    )
    # Take out a game and reset, to check updates are correct
    updated_games = user_owned_games[:-1]
    neo4j_client.update_recently_played_games(
        steamid=globals.STEAM_ID, games=updated_games
    )
    # Read all recently played games and verify
    cypher = """
        MATCH (u:User {steamId: $steamid})-[r:RECENTLY_PLAYED]->(g:Game)
        RETURN g.appId as appid, r.recentPlaytime as playtime
    """
    result = neo4j_client._read(cypher, steamid=globals.STEAM_ID)
    assert len(result) == len(updated_games)
    for expected_game in updated_games:
        assert not result.loc[
            (result["appid"] == expected_game["appid"])
            & (result["playtime"] == expected_game["playtime_2weeks"])
        ].empty
