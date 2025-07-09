from vapor import clients
from vapor.utils import utils


def populate_from_friends(
    steam_client: clients.SteamClient,
    neo4j_client: clients.Neo4jClient,
    steam_id: str | None = None,
    hops: int = 2,
    friend_limit: int | None = None,
    game_limit: int | None = None,
) -> None:
    """Populate the neo4j database for the primary user
    by recursively discovering friends and their owned games
    until `hops` is reached.

    Args:
        steam_client (SteamClient): The `SteamClient` instance to query
            the SteamWebAPI.
        neo4j_client (Neo4jClient): The `Neo4jClient` instance to query
            the Neo4j GraphDB.
        steam_id (optional, str): The Steam user ID number (as a string)
            to populate data from. Leave as None to populate from the
            `steam_client` primary user as the central node. The method
            will handle recursive calls through with `steam_id` values
            from the friends list. Defaults to None.
        hops (optional, int): The number of hops, i.e. recursive calls
            to `populate_from_friends`, outward from the primary user
            before ceasing execution. Defaults to 2.
        friend_limit (optional, int): Limit the amount of friends to include
            per friends list query. If None, all friends will be included.
            Defaults to None.
        game_limit (optional, int): Limit the amount of games to include
            per games list query. If None, all games will be included.
            Defaults to None.
    """
    if hops < 0:
        return
    if not steam_id:
        # Get primary user and add to db
        primary_user = steam_client.get_primary_user_details(
            ["steam_id", "personaname"]
        )
        neo4j_client.add_user(**primary_user)
        neo4j_client.set_primary_user(primary_user["steam_id"])
        # Recurse using primary user id
        return populate_from_friends(
            steam_client,
            neo4j_client,
            primary_user["steam_id"],
            hops,
            friend_limit,
            game_limit,
        )

    # Get games for this user and add to db
    games = list(
        steam_client.get_user_owned_games(steam_id, ["appid", "name"], limit=game_limit)
    )
    neo4j_client.add_owned_games(steam_id, games)
    # Add genres for all games
    neo4j_client.add_genres(games)

    # Get friends list, add to db and recurse for each (decrement hops)
    friends = list(
        steam_client.get_user_friends(
            steam_client.steam_id, ["steam_id", "personaname"], limit=friend_limit
        )
    )
    neo4j_client.add_friends(steam_id, friends)
    for friend in friends:
        return populate_from_friends(
            steam_client,
            neo4j_client,
            friend["steam_id"],
            hops - 1,
            friend_limit,
            game_limit,
        )


def main(**kwargs) -> None:
    """Entry point to populate data. Initializes steam/neo4j from env vars."""
    utils.load_dotenv()
    steam_client = clients.SteamClient.from_env()
    neo4j_client = clients.Neo4jClient.from_env()
    return populate_from_friends(steam_client, neo4j_client, steam_id=None, **kwargs)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Populate neo4j database with steam data for Vapor"
    )
    parser.add_argument(
        "-n",
        "--hops",
        type=int,
        help="Number of hops to populate with. Defaults to 2.",
        default=2,
    )
    parser.add_argument(
        "-F",
        "--friend-limit",
        type=int,
        help="Number of friends to limit each friends list query to."
        + " If None, all friends will be included. Defaults to None.",
        default=None,
    )
    parser.add_argument(
        "-G",
        "--game-limit",
        type=int,
        help="Number of games to limit each games list query to."
        + " If None, all games will be included. Defaults to None.",
        default=None,
    )
    args = parser.parse_args()
    main(**args.__dict__)
