from vapor.utils.neo4jutils import Neo4jClient
from vapor.utils.steamutils import SteamClient


def main() -> None:
    neo4j_client = Neo4jClient.from_env()
    steam_client = SteamClient.from_env()

    # TODO: Refactor name to personaname in neo4j or map to name in steam
    # then we can do something like .add_user(**user)
    primary_user = steam_client.get_primary_user_details(["steam_id", "personaname"])
    neo4j_client.add_user(primary_user["steam_id"], primary_user["personaname"])
    neo4j_client.set_primary_user(primary_user["steam_id"])

    friends = steam_client.get_user_friends(
        primary_user["steam_id"], fields=["steam_id", "personaname"]
    )
    neo4j_client.add_friends(primary_user["steam_id"], friends)

    # TODO: Games
