from __future__ import annotations
from typing import Any
import warnings

from neo4j import GraphDatabase, RoutingControl, ExperimentalWarning
import pandas as pd

from vapor.utils import utils

# Ignore Neo4j warning about experimental params in verify_connectivity()
warnings.filterwarnings("ignore", category=ExperimentalWarning)


class NotFoundException(Exception):
    pass


class Neo4jClient(object):
    """Client to perform Cypher transactions to the Neo4j GraphDB"""

    def __init__(self, uri: str, auth: tuple[str, str], database: str):
        """Initialize the client to connect to the database
        at `uri` with the `auth` combo of `(username, password)`
        """
        self.driver = GraphDatabase.driver(uri=uri, auth=auth)
        self._database = database
        self.driver.verify_connectivity(database=self._database)

    @classmethod
    def from_env(cls) -> Neo4jClient:
        """Initialize a `Neo4jClient` from default environment variables"""
        return cls(
            uri=utils.get_env_var("NEO4J_URI"),
            auth=(
                utils.get_env_var("NEO4J_USER"),
                utils.get_env_var("NEO4J_PW"),
            ),
            database=utils.get_env_var("NEO4J_DATABASE"),
        )

    def _write(self, cypher: str, **kwargs) -> None:
        """Run the `cypher` query in 'write' mode"""
        self.driver.execute_query(
            cypher, database_=self._database, routing_=RoutingControl.WRITE, **kwargs
        )

    def _read(self, cypher: str, **kwargs) -> pd.DataFrame:
        """Run the `cypher` query in 'read' mode, always transforming
        and returning the results as a dataframe
        """
        return self.driver.execute_query(
            cypher,
            database_=self._database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda r: r.to_df(),
            **kwargs,
        )

    def _set_user_constraint(self) -> None:
        cypher = """
            CREATE CONSTRAINT user_constraint IF NOT EXISTS FOR (u:User) REQUIRE (u.steamId) IS UNIQUE
        """
        self._write(cypher)

    def _set_game_constraint(self) -> None:
        cypher = """
            CREATE CONSTRAINT game_constraint IF NOT EXISTS FOR (g:Game) REQUIRE (g.appId) IS UNIQUE
        """
        self._write(cypher)

    def _get_constraints(self) -> pd.DataFrame:
        cypher = """SHOW CONSTRAINTS"""
        return self._read(cypher)

    def _set_primary_user(self, primary_steamid: str) -> None:
        """Set the primary user, i.e. central node, of the database.
        Assumes that the `User` node has already been added and will
        add the `Primary` label.

        Args:
            primary_steamid (str): The Steam user ID of the primary user.
        """

        cypher = """
            MATCH (u:User)
            WHERE u.steamId = $primary_steamid
            SET u:Primary
        """
        self._write(cypher, primary_steamid=primary_steamid)

    def get_primary_user(self) -> dict[str, Any]:
        """Get the primary user info, i.e. central node, from the database.

        Raises:
            `NotFoundException` if the primary user node cannot be found.
        """
        cypher = """
            MATCH (p:Primary)
            RETURN p.steamId as steamid, p.personaName as personaname
        """
        result = self._read(cypher)
        if result.empty:
            raise NotFoundException(
                "Unable to identify primary user. Has this database been initialized?"
            )
        return result.iloc[0].to_dict()

    @property
    def is_setup(self) -> bool:
        # Check primary user
        try:
            self.get_primary_user()
        except NotFoundException:
            print("No primary user found.")
            return False

        # Check constraints
        valid_constraints = {x + "_constraint" for x in ["game", "user"]}
        constraints = set(self._get_constraints()["name"])
        missing_constraints = valid_constraints - constraints
        if missing_constraints:
            print(f"Missing constraints: {missing_constraints}")
            return False

        return True

    def setup_from_primary_user(self, **primary_user) -> None:
        if self.is_setup:
            print("Neo4j database is setup and valid.")
            return

        print("Setting up Neo4j database with valid initial state...")
        print(f"Setting primary user: {primary_user}")
        self.add_user(**primary_user)
        self._set_primary_user(primary_user["steamid"])

        print("Setting necessary constraints...")
        self._set_user_constraint()
        self._set_game_constraint()

        # Recurse to validate success
        self.setup_from_primary_user(**primary_user)

    def add_user(self, steamid: str, personaname: str) -> None:
        """Add a `User` node with the provided properties.

        Args:
            steamid (str): The Steam user ID of the user to add.
            personaname (str): The Steam username of the user to add.
        """
        cypher = """
            MERGE (u:User {steamId: $steamid, personaName: $personaname})
        """
        self._write(cypher, steamid=steamid, personaname=personaname)

    def add_friends(self, steamid: str, friends: list[dict[str, Any]]):
        """Add the list of `friends` as `User` nodes which are friends
        with the `User` node matching `steamid`.

        Args:
            steamid (str): The Steam user ID of the user to add `friends`
                relationships to.
            friends (list[dict[str, Any]]): The list of friends each with
                parameters of `steamid` and `personaname`.
        """

        cypher = """
            MATCH (u:User {steamId: $steamid})
            UNWIND $friends AS friend
            MERGE (f:User {steamId: friend.steamid, personaName: friend.personaname})
            MERGE (u)-[:HAS_FRIEND]-(f)
        """
        self._write(cypher, steamid=steamid, friends=friends)

    def add_owned_games(self, steamid: str, games: list[dict[str, Any]]) -> None:
        """Add the list of `games` as `Game` nodes which are owned by
        the `User` node matching `steamid`.

        Args:
            steamid (str): The Steam user ID of the user to add `games`
                relationships to.
            games (list[dict[str, Any]]): The list of games each with
                parameters of `appid` and `name`.
        """
        cypher = """
            MATCH (u:User {steamId: $steamid})
            UNWIND $games AS game
            MERGE (g:Game {appId: game.appid, name: game.name})
            MERGE (u)-[:OWNS]->(g)
        """
        self._write(cypher, steamid=steamid, games=games)

    def detach_delete(self) -> None:
        """WARNING: Removes all nodes and relationships from the graph!"""
        cypher = """
            MATCH (n)
            DETACH DELETE n
        """
        warnings.warn(
            message="Removing all nodes and relationships from the graph!"
            + " This action cannote be undone",
            category=UserWarning,
        )
        self._write(cypher)

    # @staticmethod
    # def _add_genres_tx(tx: ManagedTransaction, games: list[dict[str, Any]]) -> None:
    #     """Unit of work for `add_genres` method"""
    #     cypher = """
    #         UNWIND $games AS game
    #         UNWIND game.genres AS genre
    #         MATCH (g:Game {appId: game.appid})
    #         MERGE (g)-[:HAS_GENRE]->(n:Genre {name: genre.name})
    #         WITH DISTINCT n.name AS genre_names
    #         RETURN collect(genre_names) AS genres
    #     """

    #     record = tx.run(cypher, games=games).single()
    #     if games and not record["genres"]:
    #         raise NotFoundException(f"Did not record any game genres")

    # def add_genres(self, games: list[dict[str, Any]]) -> None:
    #     """Create `Genre` nodes via relationships to the `games`
    #     which have those genre properties.

    #     Args:
    #         games (list[dict[str, Any]]): The list of games to add
    #             relationships for their genres.
    #     """
    #     self._write(self._add_genres_tx, games=games)
