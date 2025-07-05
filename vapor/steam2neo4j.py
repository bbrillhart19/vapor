from vapor import clients


def populate_from_friends(
    steam_client: clients.SteamClient,
    neo4j_client: clients.Neo4jClient,
    steam_id: str | None = None,
    hops: int = 2,
) -> None:
    """Populate the neo4j database for the primary user
    by recursively discovering friends and their owned games
    until `hops` is reached.
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
            steam_client, neo4j_client, primary_user["steam_id"], hops
        )

    # Get games for this user and add to db
    games = list(steam_client.get_user_owned_games(steam_id, ["appid", "name"]))
    neo4j_client.add_owned_games(steam_id, games)
    # Add genres for all games
    neo4j_client.add_genres(games)

    # Get friends list, add to db and recurse for each (decrement hops)
    friends = steam_client.get_user_friends(steam_client, ["steam_id", "personaname"])
    neo4j_client.add_friends(steam_id, friends)
    for friend in friends:
        return populate_from_friends(
            steam_client, neo4j_client, friend["steam_id"], hops - 1
        )


def main(hops: int = 2) -> None:
    """Entry point to populate data. Initializes steam/neo4j from env vars."""
    steam_client = clients.SteamClient.from_env()
    neo4j_client = clients.Neo4jClient.from_env()
    return populate_from_friends(steam_client, neo4j_client, hops=hops)


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
    args = parser.parse_args()
    main(**args.__dict__)
