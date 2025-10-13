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
            steam_client,
            neo4j_client,
            primary_user["steamid"],
            hops,
            limit,
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
            steam_client,
            neo4j_client,
            friend["steamid"],
            hops - 1,
            limit,
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
    for user in track(
        users_df.itertuples(),
        description="Populating games:",
        total=total_users,
    ):
        owned_games = list(
            steam_client.get_user_owned_games(
                user.steamid, fields=owned_games_fields, limit=limit
            )
        )
        neo4j_client.add_owned_games(user.steamid, owned_games)
        recently_played_games = list(
            steam_client.get_user_recently_played_games(
                user.steamid, fields=recently_played_fields, limit=limit
            )
        )
        neo4j_client.update_recently_played_games(
            steamid=user.steamid, games=recently_played_games
        )


def populate_genres(
    steam_client: clients.SteamClient,
    neo4j_client: clients.Neo4jClient,
    limit: int | None = None,
) -> None:
    """Populate the neo4j database with genres for all games
    in the database.

        Args:
        steam_client (SteamClient): The `SteamClient` instance to query
            the SteamWebAPI.
        neo4j_client (Neo4jClient): The `Neo4jClient` instance to query
            the Neo4j GraphDB.
    """
    games_df = neo4j_client.get_all_games(limit=limit)
    total_games = len(games_df)
    logger.info(f"Found {total_games} total games to populate genres from.")

    # Iterate through each game, retrieve details and add genres
    for game in track(
        games_df.itertuples(),
        description="Populating genres:",
        total=total_games,
    ):
        game_details = steam_client.get_game_details(game.appid, filters=["genres"])
        if "genres" not in game_details:
            continue
        neo4j_client.add_game_genres(game.appid, game_details["genres"])


@logger.catch
def steam2neo4j(
    hops: int = 2,
    init: bool = False,
    delete: bool = False,
    friends: bool = False,
    games: bool = False,
    genres: bool = False,
    limit: int | None = None,
) -> None:
    """Entry point to populate data. Initializes steam/neo4j from env vars."""
    logger.info("Initializing SteamClient...")
    steam_client = clients.SteamClient.from_env()
    logger.info("Initializing Neo4jClient...")
    neo4j_client = clients.Neo4jClient.from_env()

    # Setup neo4j with primary user
    if init:
        logger.info("Retrieving primary user details and setting up...")
        primary_user = steam_client.get_primary_user_details(["steamid", "personaname"])
        neo4j_client.setup_from_primary_user(**primary_user)

    # Delete everything and return
    if delete:
        neo4j_client.detach_delete()
        return

    # Check for setup before proceeding with anything else
    assert neo4j_client.is_setup, (
        f"Neo4j is not setup properly and thus cannot be populated. "
        + "Make sure you run `steam2neo4j` with `init` enabled."
    )

    # Populate friends spanning from primary user
    if friends:
        logger.info("Populating Steam users from friends lists...")
        populate_friends(
            steam_client, neo4j_client, steamid=None, hops=hops, limit=limit
        )

    # Populate games via all users (primary and friends)
    if games:
        logger.info("Populating Steam games from available Steam users...")
        populate_games(steam_client, neo4j_client, limit=limit)

    # Populate genres via all games
    if genres:
        logger.info("Populating genees from available Steam games...")
        populate_genres(steam_client, neo4j_client)

    logger.success("Completed steam2neo4j sequence >>>")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Set up and populate neo4j database with steam data for Vapor"
    )
    parser.add_argument(
        "-n",
        "--hops",
        type=int,
        help="Number of hops to populate with. Defaults to 2.",
        default=2,
    )
    parser.add_argument(
        "-i",
        "--init",
        action="store_true",
        help="Initialize the neo4j database with necessary constraints"
        + " and set up the primary user. Disabled by default.",
    )
    parser.add_argument(
        "-D",
        "--delete",
        action="store_true",
        help="WARNING: This will delete all nodes and relationships in the graph."
        + " Disabled by default.",
    )
    parser.add_argument(
        "-f",
        "--friends",
        action="store_true",
        help="Populate friends starting from primary spanning out `n_hops`."
        + " Requires prior initialized neo4j database. Disabled by default.",
    )
    parser.add_argument(
        "-g",
        "--games",
        action="store_true",
        help="Populate games via users starting from primary spanning out `n_hops`."
        + " Requires prior initialized neo4j database with friends."
        + " Disabled by default.",
    )
    parser.add_argument(
        "-G",
        "--genres",
        action="store_true",
        help="Populate all game genres for all games present in the database."
        + " Requires prior initialized neo4j database with games."
        + " Disabled by default.",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        help="Limits all populating queries (friends, games, etc.) to this value."
        + " If None, all discovered datums will be included. Defaults to None.",
        default=None,
    )

    args = parser.parse_args()
    steam2neo4j(**args.__dict__)
