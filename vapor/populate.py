from loguru import logger

from vapor.core import clients
from vapor.core.models.embeddings import VaporEmbeddings
from vapor.core.utils import steam2neo4j, model2neo4j


@logger.catch(reraise=True)
def populate_neo4j(
    hops: int = 2,
    init: bool = False,
    delete: bool = False,
    friends: bool = False,
    games: bool = False,
    genres: bool = False,
    game_descriptions: bool = False,
    embed: list[str] | None = None,
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

    # Clear everything and return
    if delete:
        neo4j_client.clear()
        return

    # Check for setup before proceeding with anything else
    assert neo4j_client.is_setup, (
        f"Neo4j is not setup properly and thus cannot be populated. "
        + "Make sure you run `populate_neo4j` with `init` enabled."
    )

    # Populate friends spanning from primary user
    if friends:
        logger.info("Populating Steam users from friends lists...")
        steam2neo4j.populate_friends(
            steam_client, neo4j_client, steamid=None, hops=hops, limit=limit
        )

    # Populate games via all users (primary and friends)
    if games:
        logger.info("Populating Steam games from available Steam users...")
        steam2neo4j.populate_games(steam_client, neo4j_client, limit=limit)

    # Populate genres via all games
    if genres:
        logger.info("Populating genres from available Steam games...")
        steam2neo4j.populate_genres(steam_client, neo4j_client)

    # Populate game descriptions for all games
    if game_descriptions:
        logger.info("Populating game descriptions for available Steam games...")
        steam2neo4j.populate_game_descriptions(steam_client, neo4j_client)

    # Embed the game descriptions and set up vector index
    if embed:
        logger.info("Setting up embedding model...")
        embedder = VaporEmbeddings.from_env()

        texts_to_embed = set(embed)
        if "game-descriptions" in texts_to_embed:
            logger.info("Embedding game descriptions and setting up vector index...")
            model2neo4j.embed_game_descriptions(embedder, neo4j_client)

    logger.success("Completed Neo4j population sequence >>>")


if __name__ == "__main__":
    import argparse
    from vapor.core.utils import utils

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
    parser.add_argument(
        "-d",
        "--game-descriptions",
        action="store_true",
        help="Populate all game description texts from 'about_the_game'"
        + " Requires prior initialized neo4j database with games."
        + " Disabled by default.",
    )
    parser.add_argument(
        "--embed",
        nargs="+",
        choices=["game-descriptions"],
        help="Texts to chunk and embed. Full texts must be"
        + " populated in neo4j prior to embedding. The currently"
        + " configured OLLAMA_EMBEDDING_MODEL="
        + f"{utils.get_env_var('OLLAMA_EMBEDDING_MODEL', '!!!NONE FOUND!!!')}",
    )

    args = parser.parse_args()

    populate_neo4j(**args.__dict__)
