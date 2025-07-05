from vapor import clients


def main() -> None:
    neo4j_client = clients.Neo4jClient.from_env()
    steam_client = clients.SteamClient.from_env()

    # TODO: Refactor name to personaname in neo4j or map to name in steam
    # then we can do something like .add_user(**user)
    # primary_user = steam_client.get_primary_user_details(["steam_id", "personaname"])
    primary_user = {
        "steam_id": steam_client.steam_id,
        "personaname": "testuser",
    }
    neo4j_client.add_user(**primary_user)
    neo4j_client.set_primary_user(primary_user["steam_id"])

    # TODO: Refactor into method to allow recurisve hops from primary user
    # like populate_from_friends
    # friends = steam_client.get_user_friends(
    #     primary_user["steam_id"], fields=["steam_id", "personaname"]
    # )
    friends = [
        {
            "steam_id": "12345",
            "personaname": "friend1",
        },
        {
            "steam_id": "678910",
            "personaname": "friend2",
        },
    ]
    print(neo4j_client.add_friends(primary_user["steam_id"], friends=[]))

    # TODO: Allow multiple genres
    # games = steam_client.get_user_owned_games(primary_user["steam_id"], ["appid", "name", "genre"])
    games = [
        {
            "appid": 1234,
            "name": "game1",
            "genres": [{"name": "genre1"}, {"name": "genre3"}],
        },
        {
            "appid": 5678,
            "name": "game2",
            "genres": [{"name": "genre1"}, {"name": "genre2"}],
        },
    ]
    print(neo4j_client.add_owned_games(primary_user["steam_id"], games=games[:1]))
    print(neo4j_client.add_genres(games))


if __name__ == "__main__":
    main()
