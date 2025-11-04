import os

from vapor.clients import SteamClient, Neo4jClient
from vapor import populate
from helpers import globals


def test_init_delete(mocker, neo4j_client: Neo4jClient):
    """Tests the `populate_neo4j` entry point, setting up and immediately clearing"""
    # Patch env vars to dev values
    mocker.patch.dict(
        os.environ,
        {
            "STEAM_API_KEY": globals.STEAM_API_KEY,
            "STEAM_ID": globals.STEAM_ID,
            "NEO4J_URI": globals.NEO4J_URI,
            "NEO4J_USER": globals.NEO4J_USER,
            "NEO4J_PW": globals.NEO4J_PW,
            "NEO4J_DATABASE": globals.NEO4J_DATABASE,
        },
    )
    # Patch steam client primary user details
    mocker.patch.object(
        SteamClient,
        "get_primary_user_details",
        return_value={
            "steamid": globals.STEAM_ID,
            "personaname": "user0",
        },
    )
    # Run populate with init and delete
    populate.populate_neo4j(init=True, delete=True)
    # Ensure DB is empty
    result = neo4j_client.get_all_users()
    assert result.empty
    result = neo4j_client._get_constraints()
    assert result.empty


def test_populate(
    mocker,
    neo4j_client: Neo4jClient,
    steam_friends: dict[str, list[dict]],
    steam_games: dict[int, dict],
    steam_owned_games: dict[str, list[dict]],
):
    """Tests the `populate_neo4j` entry point with full sequence"""
    # Patch env vars to dev values
    mocker.patch.dict(
        os.environ,
        {
            "STEAM_API_KEY": globals.STEAM_API_KEY,
            "STEAM_ID": globals.STEAM_ID,
            "NEO4J_URI": globals.NEO4J_URI,
            "NEO4J_USER": globals.NEO4J_USER,
            "NEO4J_PW": globals.NEO4J_PW,
            "NEO4J_DATABASE": globals.NEO4J_DATABASE,
        },
    )
    # Patch steam client primary user details
    mocker.patch.object(
        SteamClient,
        "get_primary_user_details",
        return_value={
            "steamid": globals.STEAM_ID,
            "personaname": "user0",
        },
    )

    # Mock the steam client to return friends per user
    def mocked_friends(steamid: str, *args, **kwargs):
        friends = steam_friends[steamid]
        if "limit" in kwargs:
            friends = friends[: kwargs["limit"]]
        for friend in friends:
            yield friend

    mocker.patch.object(
        SteamClient,
        "get_user_friends",
        side_effect=mocked_friends,
    )

    # Mock the steam client to return owned and
    # recently played games for each user
    def mocked_owned_games(steamid: str, *args, **kwargs):
        owned_games = steam_owned_games[steamid]
        if "limit" in kwargs:
            owned_games = owned_games[: kwargs["limit"]]
        for game in owned_games:
            yield game

    mocker.patch.object(
        SteamClient,
        "get_user_owned_games",
        side_effect=mocked_owned_games,
    )
    # Just use the same mocked function for recently played
    mocker.patch.object(
        SteamClient,
        "get_user_recently_played_games",
        side_effect=mocked_owned_games,
    )

    # Mock the steam client to return genres for each game
    def mocked_game_genres(appid: int, *args, **kwargs):
        return steam_games[appid]["genres"]

    mocker.patch.object(
        SteamClient,
        "get_game_genres",
        side_effect=mocked_game_genres,
    )

    # Set small limit for brevity
    limit = 2
    # Run the population sequence
    populate.populate_neo4j(
        hops=2, init=True, friends=True, games=True, genres=True, limit=limit
    )

    # Verify expected friendships (first hop=primary user)
    cypher = """
        MATCH (p:Primary)-[:HAS_FRIEND]->(u:User)
        RETURN u.steamId as steamid
    """
    result = neo4j_client._read(cypher)
    result_steamids = set(result["steamid"])
    expected_steamids = set(
        x["steamid"] for x in steam_friends[globals.STEAM_ID][:limit]
    )
    assert not expected_steamids - result_steamids

    # Verify second hop friendships
    cypher = """
        MATCH (u:User {steamId: $steamid})-[:HAS_FRIEND]->(f:User)
        RETURN f.steamId as steamid
    """
    for steamid in expected_steamids:
        result = neo4j_client._read(cypher, steamid=steamid)
        result_steamids = set(result["steamid"])
        _expected_steamids = set(x["steamid"] for x in steam_friends[steamid][:limit])
        assert not _expected_steamids - result_steamids

    # Verify the expected games relationships
    all_users = neo4j_client.get_all_users()
    owned_games_cypher = """
        MATCH (u:User {steamId: $steamid})-[r:OWNS_GAME]->(g:Game)
        RETURN g.appId as appid, g.name as name, r.playtime as playtime_forever
    """
    recently_played_cypher = """
        MATCH (u:User {steamId: $steamid})-[r:RECENTLY_PLAYED]->(g:Game)
        RETURN g.appId as appid, g.name as name, r.recentPlaytime as playtime_2weeks
    """
    for user in all_users.itertuples():
        steamid = user.steamid
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

    # Verify the expected genres
    all_games = neo4j_client.get_all_games()
    cypher = """
        MATCH (g:Game {appId: $appid})-[:HAS_GENRE]->(n:Genre)
        RETURN n.genreId as id, n.description as description
    """
    for game in all_games.itertuples():
        result = neo4j_client._read(cypher, appid=game.appid)
        expected_genres = steam_games[game.appid]["genres"]
        for expected_genre in expected_genres:
            assert not result.loc[
                (result["id"] == expected_genre["id"])
                & (result["description"] == expected_genre["description"])
            ].empty
