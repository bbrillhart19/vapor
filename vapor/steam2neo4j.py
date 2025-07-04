from vapor import clients


def main() -> None:
    neo4j_client = clients.Neo4jClient.from_env()
    steam_client = clients.SteamClient.from_env()

    # TODO: Refactor name to personaname in neo4j or map to name in steam
    # then we can do something like .add_user(**user)
    primary_user = steam_client.get_primary_user_details(["steam_id", "personaname"])
    neo4j_client.add_user(primary_user["steam_id"], primary_user["personaname"])
    neo4j_client.set_primary_user(primary_user["steam_id"])

    # TODO: Refactor into method to allow recurisve hops from primary user
    # like populate_from_friends
    friends = steam_client.get_user_friends(
        primary_user["steam_id"], fields=["steam_id", "personaname"]
    )
    neo4j_client.add_friends(primary_user["steam_id"], friends)

    games = steam_client.get_user_owned_games(primary_user["steam_id"], ["appid", "name", "genre"])
    neo4j_client.add_owned_games(primary_user["steam_id"], games)
    neo4j_client.add_genres(games)
