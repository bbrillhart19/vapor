from rich.progress import track
from loguru import logger

from vapor import clients


def populate_friends(
    steam_client: clients.SteamClient,
    neo4j_client: clients.Neo4jClient,
    steamid: str | None = None,
    hops: int = 2,
    limit: int | None = None,
) -> None:
    """Populate the neo4j database for the primary user
    by recursively discovering friends until `hops` is reached.

    Args:
        steam_client (SteamClient): The `SteamClient` instance to query
            the SteamWebAPI.
        neo4j_client (Neo4jClient): The `Neo4jClient` instance to query
            the Neo4j GraphDB.
        steamid (optional, str): The Steam user ID number (as a string)
            to populate data from. Leave as None to populate from the
            `steam_client` primary user as the central node. The method
            will handle recursive calls through with `steamid` values
            from the friends list. Defaults to None.
        hops (optional, int): The number of hops, i.e. recursive calls
            to `populate_from_friends`, outward from the primary user
            before ceasing execution. Defaults to 2.
        limit (optional, int): Limit the amount of friends to include
            per friends list query. If None, all friends will be included.
            Defaults to None.
    """

    if hops < 0:
        return

    if not steamid:
        # Get primary user steam id from neo4j
        primary_user = neo4j_client.get_primary_user()

        # Recurse using primary user id
        return populate_friends(
            steam_client, neo4j_client, primary_user["steamid"], hops, limit,
        )

    # Get friends list, add to db and recurse for each (decrement hops)
    friends = list(
        steam_client.get_user_friends(steamid, ["steamid", "personaname"], limit=limit)
    )
    # Avoid adding friend relationships past the allowed hops
    if hops > 0:
        logger.info(
            f"Adding ({len(friends)}) friends from user={steamid}"
            + f" [{hops} hop(s) remaining]"
        )
        neo4j_client.add_friends(steamid, friends)

    for friend in friends:
        populate_friends(
            steam_client, neo4j_client, friend["steamid"], hops - 1, limit,
        )


def populate_games(
    steam_client: clients.SteamClient,
    neo4j_client: clients.Neo4jClient,
    limit: int | None = None,
) -> None:
    """Populate the neo4j database with games from the games list
    for each user present in the database, as well as their
    recently played games.

    Args:
        steam_client (SteamClient): The `SteamClient` instance to query
            the SteamWebAPI.
        neo4j_client (Neo4jClient): The `Neo4jClient` instance to query
            the Neo4j GraphDB.
        limit (optional, int): Limit the amount of games to include
            per user query. If None, all games will be included.
            Defaults to None.
    """
    # The fields we want to extract for the neo4j relationships
    owned_games_fields = [
        "appid",
        "name",
        "playtime_forever",
    ]
    recently_played_fields = [
        "appid",
        "playtime_2weeks",
    ]
    # Get all users from the database
    users_df = neo4j_client.get_all_users()
    total_users = len(users_df)
    logger.info(f"Found {total_users} total users to populate games from.")
    # Iterate through each user and add their games
    for steamid in track(
        users_df.steamid, description="Populating games:", total=total_users
    ):
        owned_games = list(
            steam_client.get_user_owned_games(
                steamid, fields=owned_games_fields, limit=limit
            )
        )
        neo4j_client.add_owned_games(steamid, owned_games)
        recently_played_games = list(
            steam_client.get_user_recently_played_games(
                steamid, fields=recently_played_fields, limit=limit
            )
        )
        neo4j_client.update_recently_played_games(
            steamid=steamid, games=recently_played_games
        )


def populate_genres(
    steam_client: clients.SteamClient, neo4j_client: clients.Neo4jClient,
) -> None:
    """Populate the neo4j database with genres for all games
    in the database.

    Args:
        steam_client (SteamClient): The `SteamClient` instance to query
            the SteamWebAPI.
        neo4j_client (Neo4jClient): The `Neo4jClient` instance to query
            the Neo4j GraphDB.
    """
    games_df = neo4j_client.get_all_games()
    total_games = len(games_df)
    logger.info(f"Found {total_games} total games to populate genres from.")

    # Iterate through each game, retrieve and add genres
    for appid in track(
        games_df.appid, description="Populating genres:", total=total_games
    ):
        genres = steam_client.get_game_genres(appid)
        neo4j_client.add_game_genres(appid, genres)


def populate_game_descriptions(
    steam_client: clients.SteamClient, neo4j_client: clients.Neo4jClient,
) -> None:
    """Populate the neo4j database with game descriptions for all games
    in the database.

    Args:
        steam_client (SteamClient): The `SteamClient` instance to query
            the SteamWebAPI.
        neo4j_client (Neo4jClient): The `Neo4jClient` instance to query
            the Neo4j GraphDB.
    """
    games_df = neo4j_client.get_all_games()
    total_games = len(games_df)
    logger.info(f"Found {total_games} total games to populate descriptions for.")

    descriptions = []
    # Iterate through each game, retrieve description
    for appid in track(
        games_df.appid, description="Retrieving descriptions:", total=total_games
    ):
        game_doc = steam_client.about_the_game(appid)
        if game_doc is not None:
            descriptions.append({"appid": appid, "about_the_game": game_doc})

    # Add descriptions in batch
    logger.info(f"Adding {len(descriptions)} total game desriptions...")
    neo4j_client.add_game_descriptions(descriptions)
