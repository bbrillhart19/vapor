from __future__ import annotations
from typing import Callable, Any

from neo4j import GraphDatabase, ManagedTransaction

from vapor.utils import utils


class NotFoundException(Exception):
    pass


class Neo4jClient(object):
    def __init__(self, uri: str, auth: tuple[str, str]):
        self.driver = GraphDatabase.driver(uri=uri, auth=auth)
        self.driver.verify_connectivity()

    @classmethod
    def from_env(cls) -> Neo4jClient:
        return cls(
            uri=utils.get_env_var("NEO4J_URI"),
            auth=(utils.get_env_var("NEO4J_USER"), utils.get_env_var("NEO4J_PW"),),
        )

    def _write(self, unit_of_work: Callable, **kwargs) -> Any:
        with self.driver.session() as session:
            return session.execute_write(unit_of_work, **kwargs)

    def _read(self, unit_of_work: Callable, **kwargs) -> Any:
        with self.driver.session() as session:
            return session.execute_read(unit_of_work, **kwargs)

    @staticmethod
    def _add_user_tx(tx: ManagedTransaction, steam_id: str, personaname: str):
        cypher = """
            MERGE (u:User {steamId: $steam_id})
            SET u.personaname = $personaname
            RETURN u AS user
        """
        record = tx.run(cypher, steam_id=steam_id, personaname=personaname).single()
        if "user" not in record.keys():
            raise NotFoundException(f"Could not find user with steam_id={steam_id}")
        return record["user"]

    def add_user(self, steam_id: str, personaname: str) -> dict:
        return self._write(
            self._add_user_tx, steam_id=steam_id, personaname=personaname
        )

    @staticmethod
    def _set_primary_user_tx(tx: ManagedTransaction, primary_steam_id: str):
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
        return record["user"]

    def set_primary_user(self, primary_steam_id: str) -> dict:
        return self._write(self._set_primary_user_tx, primary_steam_id=primary_steam_id)

    @staticmethod
    def _add_friends_tx(
        tx: ManagedTransaction, steam_id: str, friends: list[dict[str, Any]]
    ):
        cypher = """
            MATCH (u:User {steamId: $steam_id})
            UNWIND $friends AS friend
            MERGE (u)-[:HAS_FRIEND]->(f:User {steamId: friend.steam_id, personaName: friend.personaname})
            RETURN collect(f) AS friends
        """
        # NOTE: Do not need both directions
        # (use directionless when with MATCH)
        record = tx.run(cypher, steam_id=steam_id, friends=friends).single()
        # TODO: Return user with friends, check if user found
        # Check for friends b/c they must at least be friends with primary
        # user in order to be found
        if friends and not record["friends"]:
            raise NotFoundException(f"Could not find user with steam_id={steam_id}")
        return record["friends"]

    def add_friends(self, steam_id: str, friends: dict[str, Any]) -> list:
        return self._write(self._add_friends_tx, steam_id=steam_id, friends=friends)

    @staticmethod
    def _add_owned_games_tx(
        tx: ManagedTransaction, steam_id: str, games: list[dict[str, Any]]
    ):
        cypher = """
            MATCH (u:User {steamId: $steam_id})
            UNWIND $games AS game
            MERGE (u)-[:OWNS]->(g:Game {appId: game.appid, name: game.name})
            RETURN collect(g) AS games
        """
        record = tx.run(cypher, steam_id=steam_id, games=games).single()
        if games and not record["games"]:
            raise NotFoundException(f"Could not find user with steam_id={steam_id}")

        return record["games"]

    def add_owned_games(self, steam_id: str, games: list[dict[str, Any]]):
        return self._write(self._add_owned_games_tx, steam_id=steam_id, games=games)

    @staticmethod
    def _add_genres_tx(tx: ManagedTransaction, games: list[dict[str, Any]]):
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
            raise NotFoundException(f"Could not find ")
        # NOTE: This only returns names, unsure how to return the nodes
        # Also, is it better to simply not return anything when writing?
        # Furthermore, how much self checking do these methods need to do?
        # Here we would need to check that all games were matched to be strict
        # if any are matched and genres added this will be fine but the non-matched
        # games silently fail. Perhaps a warning?
        return record["genres"]

    def add_genres(self, games: list[dict[str, Any]]):
        return self._write(self._add_genres_tx, games=games)
