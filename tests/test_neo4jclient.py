import os
import time

import pytest
import pandas as pd
from neo4j import Driver
from neo4j.exceptions import ServiceUnavailable

from vapor.clients import Neo4jClient
from vapor.models.embeddings import VaporEmbeddings

from helpers import globals


@pytest.mark.neo4j
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


def test_connection_failure(mocker):
    """Tests the `Neo4jClient._wait_for_connection()` logic
    when the service is unavailable. Successful connection
    is covered by everything else using a `Neo4jClient`
    """
    # NOTE: We don't want use the fixture client here, we need to mock
    # the functions first then initialize to test
    # Test connection failure with ServiceUnavailable
    mocker.patch.object(
        Driver,
        "verify_connectivity",
        side_effect=ServiceUnavailable,
    )
    # TODO: Could use pytest-time instant sleep
    with pytest.raises(ServiceUnavailable):
        client = Neo4jClient(
            uri="neo4j://test:1234",
            auth=("test", "test"),
            database="neo4j",
            timeout=1,
            sleep_duration=1,
        )


@pytest.mark.neo4j
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


@pytest.mark.neo4j
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


@pytest.mark.neo4j
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


@pytest.mark.neo4j
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


@pytest.mark.neo4j
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


@pytest.mark.neo4j
def test_add_friends(
    neo4j_client: Neo4jClient,
    steam_friends: dict[str, list[str]],
    steam_users: dict[str, dict],
):
    """Tests the `add_friends` method for a single user"""
    # Add user and their friends
    user_friends = [steam_users[steamid] for steamid in steam_friends[globals.STEAM_ID]]
    neo4j_client.add_user(steamid=globals.STEAM_ID, personaname="user0")
    neo4j_client.add_friends(steamid=globals.STEAM_ID, friends=user_friends)
    # Check the friendship relationships exist
    cypher = """
        MATCH (u:User {steamId: $steamid})-[:HAS_FRIEND]->(f:User)
        RETURN f.steamId as steamid, f.personaName as personaname
    """
    result = neo4j_client._read(cypher, steamid=globals.STEAM_ID)
    assert len(result) == len(user_friends)
    for expected_friend in user_friends:
        assert not result.loc[
            (result["steamid"] == expected_friend["steamid"])
            & (result["personaname"] == expected_friend["personaname"])
        ].empty


@pytest.mark.neo4j
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


@pytest.mark.neo4j
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


@pytest.mark.neo4j
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


@pytest.mark.neo4j
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


@pytest.mark.neo4j
def test_add_game_descriptions(neo4j_client: Neo4jClient, steam_games: dict[int, dict]):
    """Test adding game descriptions to `Game` nodes
    with `add_game_descriptions` method
    """
    # Add some games
    games = list(steam_games.values())[:2]
    cypher = """
        UNWIND $games as game
        MERGE (g:Game {appId: game.appid, name: game.name})
    """
    neo4j_client._write(cypher, games=games)
    # Create descriptions
    mock_descs = [
        {"appid": game["appid"], "about_the_game": f"This is game={game['appid']}"}
        for game in games
    ]
    # Add the descriptions
    neo4j_client.add_game_descriptions(mock_descs)
    # Read descriptions and verify
    # Verify expected descriptions
    cypher = """
        MATCH (g:Game {appId: $appid})
        WHERE g.aboutTheGame IS NOT NULL
        RETURN g.appId as appid, g.aboutTheGame as about_the_game
    """
    for game in games:
        appid = game["appid"]
        result = neo4j_client._read(cypher, appid=appid)
        assert not result.loc[
            (result["appid"] == appid)
            & (result["about_the_game"] == f"This is game={appid}")
        ].empty


@pytest.mark.neo4j
def test_set_game_description_embeddings(neo4j_client: Neo4jClient):
    """Tests creating `DescriptionChunk` nodes with embeddings"""
    # Create a dummy embedding and make chunks
    embedding = [0.5] * 20
    n_chunks_per_game = 2
    chunks: dict[int, list[dict]] = {}
    for appid in range(1000, 1003):
        chunks[appid] = []
        # Make 2 chunks per game
        for i in range(n_chunks_per_game):
            chunks[appid].append(
                {
                    "text": "text",
                    "chunkid": f"{appid}-chunk{i}",
                    "source": appid,
                    "start_index": len("text") * i,
                    "total_length": len("text"),
                    "embedding": embedding,
                }
            )

    # Add games
    games = [{"appid": appid} for appid in chunks]
    cypher = """
        UNWIND $games as game
        MERGE (g:Game {appId: game.appid})
    """
    neo4j_client._write(cypher, games=games)

    # Set the game description embeddings
    for appid, _chunks in chunks.items():
        neo4j_client.set_game_description_embeddings(appid, _chunks)

    # Check embeddings ('text' key should not be present)
    cypher = """
        MATCH (g:Game)-[:HAS_DESCRIPTION_CHUNK]->(c:DescriptionChunk)
        RETURN 
            g.appId as appid,
            c.text as text,
            c.chunkId as chunkid,
            c.startIndex as start_index,
            c.source as source,
            c.totalLength as total_length,
            c.embedding as embedding
        """
    result = neo4j_client._read(cypher)
    assert not result["text"].any()
    for appid, _chunks in chunks.items():
        rows = result.loc[result["appid"] == appid]
        assert len(rows) == len(_chunks)
        for row in rows.itertuples():
            assert isinstance(row.start_index, int)
            assert row.chunkid.startswith(str(row.appid))
            assert row.source == appid
            assert row.total_length > 0
            assert len(row.embedding) == len(embedding)


@pytest.mark.neo4j
def test_set_vector_index(neo4j_client: Neo4jClient):
    """Tests setting a vector index on a node parameter with `Neo4jClient`"""
    neo4j_client._set_vector_index(
        index_name="test",
        node="Test",
        embedding_dimension=10,
    )
    cypher = """SHOW VECTOR INDEXES"""
    result = neo4j_client._read(cypher)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["name"] == "test"
    assert row.state == "ONLINE"
    assert row.labelsOrTypes == ["Test"]
    assert row.properties == ["embedding"]


@pytest.mark.neo4j
def test_set_game_description_vector_index(neo4j_client: Neo4jClient):
    """Tests setting the game description vector index
    on all `DescriptionChunk` nodes with `embedding` attribute
    """
    neo4j_client.set_game_description_vector_index(embedding_dimension=10)
    cypher = """SHOW VECTOR INDEXES"""
    result = neo4j_client._read(cypher)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["name"] == "game_description_index"
    assert row.state == "ONLINE"
    assert row.labelsOrTypes == ["DescriptionChunk"]
    assert row.properties == ["embedding"]


def test_search_game_by_name(neo4j_client: Neo4jClient):
    """Tests searching `neo4j` by game names, which potentially
    are not an exact match to actual application names
    """
    appid = 1000
    actual_name = "Test Game II"
    search_name = "test game"
    # No games present, should return empty
    result = neo4j_client.search_game_by_name(search_name)
    assert result.empty

    # Add the test game with actual_name, should return a single match
    cypher = """
        MERGE (g:Game {appId: $appid, name: $name})
    """
    neo4j_client._write(cypher, appid=appid, name=actual_name)
    result = neo4j_client.search_game_by_name(search_name)
    assert len(result) == 1
    assert result.iloc[0]["appid"] == appid
    assert result.iloc[0]["name"] == actual_name
    assert "distance" in result.columns

    # Add an additional game that should be a better match
    actual_name2 = "Test Game"
    neo4j_client._write(cypher, appid=appid + 1, name=actual_name2)
    result = neo4j_client.search_game_by_name(search_name)
    assert len(result) == 2
    assert result.iloc[0]["appid"] == appid + 1
    assert result.iloc[0]["name"] == actual_name2
    assert result.iloc[0]["distance"] < result.iloc[1]["distance"]


@pytest.mark.neo4j
def test_game_descriptions_semantic_search(
    mock_embedder: VaporEmbeddings, neo4j_client: Neo4jClient
):
    """Tests semantic search of game descriptions"""
    # Set up vector index
    neo4j_client.set_game_description_vector_index(
        embedding_dimension=mock_embedder.embedding_size
    )
    # Add a game with a description chunk + embedding
    appid = 1000
    name = "Test"
    about_the_game = "This is a test game"

    embedding = mock_embedder.embed_documents([about_the_game])[0]
    cypher = """
        MERGE (g:Game {appId: $appid, name: $name, aboutTheGame: $about_the_game})
        MERGE (g)-[:HAS_DESCRIPTION_CHUNK]-(c:DescriptionChunk {
            source: g.appId,
            totalLength: $length,
            startIndex: 0,
            embedding: $embedding
        })
    """
    neo4j_client._write(
        cypher,
        appid=appid,
        name=name,
        about_the_game=about_the_game,
        length=len(about_the_game),
        embedding=embedding,
    )

    # Run semantic search with same embedding, should return same mock chunk
    result = neo4j_client.game_descriptions_semantic_search(
        embedding=embedding,
        n_neighbors=1,
        min_score=0.0,
    )
    assert not result.empty
    row = result.iloc[0]
    assert row["name"] == name
    assert row["appid"] == appid
    assert row["desc"] == about_the_game
    assert row["score"] > 0
