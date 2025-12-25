import os

import pytest

from vapor.clients import SteamClient, Neo4jClient
from vapor.utils import steam2neo4j
from helpers import globals


@pytest.mark.neo4j
def test_populate_friends(
    mocker,
    steam_client: SteamClient,
    neo4j_client: Neo4jClient,
    steam_users: dict[str, dict],
    steam_friends: dict[str, list[dict]],
):
    """Tests populating friends from Steam to Neo4j"""
    # First set up neo4j and primary user
    neo4j_client.setup_from_primary_user(steamid=globals.STEAM_ID, personaname="user0")

    # Mock the steam client to return friends per user
    # Mock the steam client to return friends per user
    def mocked_friends(steamid: str, *args, **kwargs):
        friends = steam_friends[steamid]
        if "limit" in kwargs:
            friends = friends[: kwargs["limit"]]
        for friendid in friends:
            yield steam_users[friendid]

    mocker.patch.object(
        SteamClient, "get_user_friends", side_effect=mocked_friends,
    )
    # Run the friends population method w/ a small limit to ensure brevity
    limit = 2
    steam2neo4j.populate_friends(
        steam_client, neo4j_client, steamid=None, hops=2, limit=limit
    )
    # Verify expected friendships (first hop=primary user)
    cypher = """
        MATCH (p:Primary)-[:HAS_FRIEND]->(u:User)
        RETURN u.steamId as steamid
    """
    result = neo4j_client._read(cypher)
    result_steamids = set(result["steamid"])
    expected_steamids = set(
        friend_id for friend_id in steam_friends[globals.STEAM_ID][:limit]
    )
    assert not expected_steamids - result_steamids
    # Verify second hop friendships
    # NOTE: It's important to use the -[]- bidirectional notation here
    # to get both ends of each friendship
    cypher = """
        MATCH (u:User {steamId: $steamid})-[:HAS_FRIEND]-(f:User)
        RETURN f.steamId as steamid
    """
    for steamid in expected_steamids:
        result = neo4j_client._read(cypher, steamid=steamid)
        result_steamids = set(result["steamid"])
        _expected_steamids = set(
            friend_id for friend_id in steam_friends[steamid][:limit]
        )
        assert not _expected_steamids - result_steamids


@pytest.mark.neo4j
def test_populate_games(
    mocker,
    steam_client: SteamClient,
    neo4j_client: Neo4jClient,
    steam_owned_games: dict[str, list[dict]],
):
    """Tests populating user-owned games from Steam to Neo4j"""
    # Add some users to populate games from
    limit = 2
    steamids = list(steam_owned_games.keys())[:limit]
    cypher = """
        UNWIND $steamids as steamid
        MERGE (u:User {steamId: steamid})
    """
    neo4j_client._write(cypher, steamids=steamids)

    # Mock the steam client to return owned and
    # recently played games for each user
    def mocked_owned_games(steamid: str, *args, **kwargs):
        owned_games = steam_owned_games[steamid]
        if "limit" in kwargs:
            owned_games = owned_games[: kwargs["limit"]]
        for game in owned_games:
            yield game

    mocker.patch.object(
        SteamClient, "get_user_owned_games", side_effect=mocked_owned_games,
    )
    # Just use the same mocked function for recently played
    mocker.patch.object(
        SteamClient, "get_user_recently_played_games", side_effect=mocked_owned_games,
    )
    # Run the games population method
    steam2neo4j.populate_games(steam_client, neo4j_client, limit=limit)
    # Verify the expected games relationships
    owned_games_cypher = """
        MATCH (u:User {steamId: $steamid})-[r:OWNS_GAME]->(g:Game)
        RETURN g.appId as appid, g.name as name, r.playtime as playtime_forever
    """
    recently_played_cypher = """
        MATCH (u:User {steamId: $steamid})-[r:RECENTLY_PLAYED]->(g:Game)
        RETURN g.appId as appid, g.name as name, r.recentPlaytime as playtime_2weeks
    """
    for steamid in steamids:
        expected_games = steam_owned_games[steamid][:limit]
        owned_result = neo4j_client._read(owned_games_cypher, steamid=steamid)
        recently_played_result = neo4j_client._read(
            recently_played_cypher, steamid=steamid
        )
        for game in expected_games:
            assert not owned_result.loc[
                (owned_result["appid"] == game["appid"])
                & (owned_result["name"] == game["name"])
                & (owned_result["playtime_forever"] == game["playtime_forever"])
            ].empty
            assert not recently_played_result.loc[
                (recently_played_result["appid"] == game["appid"])
                & (recently_played_result["name"] == game["name"])
                & (recently_played_result["playtime_2weeks"] == game["playtime_2weeks"])
            ].empty


@pytest.mark.neo4j
def test_populate_genres(
    mocker,
    steam_client: SteamClient,
    neo4j_client: Neo4jClient,
    steam_games: dict[int, dict],
):
    """Tests populating game genres from Steam to Neo4j"""
    # Add some games to populate genres from
    limit = 2
    games = list(steam_games.values())[:limit]
    cypher = """
        UNWIND $games as game
        MERGE (g:Game {appId: game.appid})
    """
    neo4j_client._write(cypher, games=games)

    # Mock the steam client to return genres for each game
    def mocked_game_genres(appid: int, *args, **kwargs):
        # Test no genres for the first game
        if appid == games[0]["appid"]:
            return []
        return steam_games[appid]["genres"]

    mocker.patch.object(
        SteamClient, "get_game_genres", side_effect=mocked_game_genres,
    )
    # Run the genres population method
    steam2neo4j.populate_genres(steam_client, neo4j_client)
    # Verify the expected genres
    cypher = """
        MATCH (g:Game {appId: $appid})-[:HAS_GENRE]->(n:Genre)
        RETURN n.genreId as id, n.description as description
    """
    for i, game in enumerate(games):
        result = neo4j_client._read(cypher, appid=game["appid"])
        # First game should not exist
        if i == 0:
            assert result.empty
            continue
        for expected_genre in game["genres"]:
            assert not result.loc[
                (result["id"] == expected_genre["id"])
                & (result["description"] == expected_genre["description"])
            ].empty


@pytest.mark.neo4j
def test_populate_game_descriptions(
    mocker,
    steam_client: SteamClient,
    neo4j_client: Neo4jClient,
    steam_games: dict[int, dict],
):
    """Tests populating game genres from Steam to Neo4j"""
    # Add some games to populate genres from
    limit = 2
    games = list(steam_games.values())[:limit]
    cypher = """
        UNWIND $games as game
        MERGE (g:Game {appId: game.appid})
    """
    neo4j_client._write(cypher, games=games)

    # Mock the steam client to return description for each game
    def mocked_game_description(appid: int, *args, **kwargs):
        # Test no description for the first game
        if appid == games[0]["appid"]:
            return None
        return f"Game Description for {appid}"

    mocker.patch.object(
        SteamClient, "about_the_game", side_effect=mocked_game_description,
    )
    # Run the game descriptions population method
    steam2neo4j.populate_game_descriptions(steam_client, neo4j_client)
    # Verify the expected descriptions
    cypher = """
        MATCH (g:Game {appId: $appid})
        WHERE g.aboutTheGame IS NOT NULL
        RETURN g.appId as appid, g.aboutTheGame as about_the_game
    """
    for i, game in enumerate(games):
        result = neo4j_client._read(cypher, appid=game["appid"])
        # First game should not exist
        if i == 0:
            assert result.empty
            continue
        assert not result.loc[
            (result["appid"] == game["appid"])
            & (result["about_the_game"] == f"Game Description for {game['appid']}")
        ].empty
