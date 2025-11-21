import os

import pytest
from langchain_ollama import OllamaEmbeddings

from vapor.clients import SteamClient, Neo4jClient
from vapor import populate
from vapor.models import embeddings
from helpers import globals


@pytest.mark.neo4j
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


@pytest.mark.neo4j
def test_populate(
    mocker,
    neo4j_client: Neo4jClient,
    steam_users: dict[str, dict],
    steam_friends: dict[str, list[str]],
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
        for friendid in friends:
            yield steam_users[friendid]

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

    # Mock the steam client to return description for each game
    def mocked_game_description(appid: int, *args, **kwargs):
        return f"Game Description for {appid}"

    mocker.patch.object(
        SteamClient,
        "about_the_game",
        side_effect=mocked_game_description,
    )

    # Set up mocks for embedding model
    embedding_size = embeddings.EMBEDDING_PARAMS[
        embeddings.DEFAULT_OLLAMA_EMBEDDING_MODEL
    ]["embedding_size"]

    def mock_embed_docs(texts: list[str], *args, **kwargs) -> list[list[float]]:
        return [[0.5] * embedding_size] * len(texts)

    mocker.patch.object(
        OllamaEmbeddings,
        "_set_clients",
        return_value=None,
    )

    mocker.patch.object(
        OllamaEmbeddings,
        "embed_documents",
        side_effect=mock_embed_docs,
    )

    # Set small limit for brevity
    limit = 2
    # Run the population sequence
    populate.populate_neo4j(
        hops=2,
        init=True,
        friends=True,
        games=True,
        genres=True,
        game_descriptions=True,
        embed=["game-descriptions"],
        limit=limit,
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
    for steamid in all_users["steamid"]:
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
    for appid in all_games["appid"]:
        result = neo4j_client._read(cypher, appid=appid)
        expected_genres = steam_games[appid]["genres"]
        for expected_genre in expected_genres:
            assert not result.loc[
                (result["id"] == expected_genre["id"])
                & (result["description"] == expected_genre["description"])
            ].empty

    # Verify expected descriptions
    cypher = """
        MATCH (g:Game {appId: $appid})
        WHERE g.aboutTheGame IS NOT NULL
        RETURN g.appId as appid, g.aboutTheGame as about_the_game
    """
    for appid in all_games["appid"]:
        result = neo4j_client._read(cypher, appid=appid)
        assert not result.loc[
            (result["appid"] == appid)
            & (result["about_the_game"] == f"Game Description for {appid}")
        ].empty

    # Verify embeddings
    cypher = """
        MATCH (g:Game)-[:HAS_DESCRIPTION_CHUNK]->(c:DescriptionChunk)
        RETURN 
            g.appId as appid,
            c.chunkId as chunk_id,
            c.startIndex as start_index,
            c.source as source,
            c.totalLength as total_length,
            c.embedding as embedding
        """
    result = neo4j_client._read(cypher)
    for appid in all_games["appid"]:
        rows = result.loc[result["appid"] == appid]
        assert not rows.empty, f"{appid}"
        for row in rows.itertuples():
            assert isinstance(row.start_index, int)
            assert row.chunk_id.startswith(str(row.appid))
            assert row.source == appid
            assert row.total_length > 0
            assert len(row.embedding) == embedding_size
