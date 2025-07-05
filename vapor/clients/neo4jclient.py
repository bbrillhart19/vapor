from __future__ import annotations
from typing import Callable, Any

from neo4j import GraphDatabase, ManagedTransaction

from vapor.utils import utils


class NotFoundException(Exception):
    pass


class Neo4jClient(object):
    """Client to perform Cypher transactions to the Neo4j GraphDB"""

    def __init__(self, uri: str, auth: tuple[str, str]):
        """Initialize the client to connect to the database
        at `uri` with the `auth` combo of `(username, password)`
        """
        self.driver = GraphDatabase.driver(uri=uri, auth=auth)
        self.driver.verify_connectivity()

    @classmethod
    def from_env(cls) -> Neo4jClient:
        """Initialize a `Neo4jClient` from default environment variables"""
        return cls(
            uri=utils.get_env_var("NEO4J_URI"),
            auth=(
                utils.get_env_var("NEO4J_USER"),
                utils.get_env_var("NEO4J_PW"),
            ),
        )

    def _write(self, unit_of_work: Callable, **kwargs) -> Any:
        """Execute the `unit_of_work` write transaction with
        parameters from `**kwargs`
        """
        with self.driver.session() as session:
            return session.execute_write(unit_of_work, **kwargs)

    def _read(self, unit_of_work: Callable, **kwargs) -> Any:
        """Execute the `unit_of_work` read transaction with
        parameters from `**kwargs`
        """
        with self.driver.session() as session:
            return session.execute_read(unit_of_work, **kwargs)

    @staticmethod
    def _add_user_tx(tx: ManagedTransaction, steam_id: str, personaname: str) -> None:
        """Unit of work for `add_user` method"""
        cypher = """
            MERGE (u:User {steamId: $steam_id})
            SET u.personaname = $personaname
            RETURN u AS user
        """
        record = tx.run(cypher, steam_id=steam_id, personaname=personaname).single()
        if "user" not in record.keys():
            raise NotFoundException(f"Could not find user with steam_id={steam_id}")

    def add_user(self, steam_id: str, personaname: str) -> None:
        """Add a `User` node with the provided properties.

        Args:
            steam_id (str): The Steam user ID of the user to add.
            personaname (str): The Steam username of the user to add.
        """
        self._write(self._add_user_tx, steam_id=steam_id, personaname=personaname)

    @staticmethod
    def _set_primary_user_tx(tx: ManagedTransaction, primary_steam_id: str) -> None:
        """Unit of work for `set_primary_user` method"""
        cypher = """
            MATCH (u:User)
            WHERE u.steamId = $primary_steam_id
            SET u:Primary
            RETURN u AS user
        """
        record = tx.run(cypher, primary_steam_id=primary_steam_id).single()
        if "user" not in record.keys():
            raise NotFoundException(
                f"Could not find user with steam_id={primary_steam_id}"
            )

    def set_primary_user(self, primary_steam_id: str) -> None:
        """Set the primary user, i.e. central node, of the database.
        Assumes that the `User` node has already been added and will
        add the `Primary` label.

        Args:
            primary_steam_id (str): The Steam user ID of the primary user.
        """
        self._write(self._set_primary_user_tx, primary_steam_id=primary_steam_id)

    @staticmethod
    def _add_friends_tx(
        tx: ManagedTransaction, steam_id: str, friends: list[dict[str, Any]]
    ) -> None:
        """Unit of work for `add_friends` method"""
        cypher = """
            MATCH (u:User {steamId: $steam_id})
            UNWIND $friends AS friend
            MERGE (u)-[:HAS_FRIEND]->(f:User {steamId: friend.steam_id, personaName: friend.personaname})
            RETURN collect(f) AS friends
        """
        # NOTE: Do not need both directions
        # (use directionless when with MATCH)
        record = tx.run(cypher, steam_id=steam_id, friends=friends).single()
        # Check for friends b/c they must at least be friends with primary
        # user in order to be found
        if friends and not record["friends"]:
            raise NotFoundException(f"Could not find user with steam_id={steam_id}")

    def add_friends(self, steam_id: str, friends: list[dict[str, Any]]):
        """Add the list of `friends` as `User` nodes which are friends
        with the `User` node matching `steam_id`.

        Args:
            steam_id (str): The Steam user ID of the user to add `friends`
                relationships to.
            friends (list[dict[str, Any]]): The list of friends each with
                parameters of `steam_id` and `personaname`.
        """
        self._write(self._add_friends_tx, steam_id=steam_id, friends=friends)

    @staticmethod
    def _add_owned_games_tx(
        tx: ManagedTransaction, steam_id: str, games: list[dict[str, Any]]
    ) -> None:
        """Unit of work for `add_owned_games` method"""
        cypher = """
            MATCH (u:User {steamId: $steam_id})
            UNWIND $games AS game
            MERGE (u)-[:OWNS]->(g:Game {appId: game.appid, name: game.name})
            RETURN collect(g) AS games
        """
        record = tx.run(cypher, steam_id=steam_id, games=games).single()
        if games and not record["games"]:
            raise NotFoundException(f"Could not find user with steam_id={steam_id}")

    def add_owned_games(self, steam_id: str, games: list[dict[str, Any]]) -> None:
        """Add the list of `games` as `Game` nodes which are owned by
        the `User` node matching `steam_id`.

        Args:
            steam_id (str): The Steam user ID of the user to add `games`
                relationships to.
            games (list[dict[str, Any]]): The list of games each with
                parameters of `appid` and `name`.
        """
        self._write(self._add_owned_games_tx, steam_id=steam_id, games=games)

    @staticmethod
    def _add_genres_tx(tx: ManagedTransaction, games: list[dict[str, Any]]) -> None:
        """Unit of work for `add_genres` method"""
        cypher = """
            UNWIND $games AS game
            UNWIND game.genres AS genre
            MATCH (g:Game {appId: game.appid})
            MERGE (g)-[:HAS_GENRE]->(n:Genre {name: genre.name})
            WITH DISTINCT n.name AS genre_names
            RETURN collect(genre_names) AS genres
        """

        record = tx.run(cypher, games=games).single()
        if games and not record["genres"]:
            raise NotFoundException(f"Did not record any game genres")

    def add_genres(self, games: list[dict[str, Any]]) -> None:
        """Create `Genre` nodes via relationships to the `games`
        which have those genre properties.

        Args:
            games (list[dict[str, Any]]): The list of games to add
                relationships for their genres.
        """
        self._write(self._add_genres_tx, games=games)
