from __future__ import annotations
from typing import Callable, Any

from neo4j import GraphDatabase

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
            auth=(
                utils.get_env_var("NEO4J_USER"),
                utils.get_env_var("NEO4J_PW"),
            ),
        )

    def _write(self, unit_of_work: Callable, **kwargs) -> Any:
        with self.driver.session() as session:
            return session.execute_write(unit_of_work, **kwargs)

    def _read(self, unit_of_work: Callable, **kwargs) -> Any:
        with self.driver.session() as session:
            return session.execute_read(unit_of_work, **kwargs)

    @staticmethod
    def _add_user_tx(tx, steam_id: str, name: str):
        cypher = """
            MERGE (u:User {steamId: $steam_id})
            SET u.name = $name
            RETURN u AS user
        """
        return tx.run(cypher, steam_id=steam_id, name=name).single()

    def add_user(self, steam_id: str, name: str) -> dict:
        record = self._write(self._add_user_tx, steam_id=steam_id, name=name)
        if not record:
            raise NotFoundException(f"Could not find user with steam_id={steam_id}")
        return record["user"]

    @staticmethod
    def _set_primary_user_tx(tx, primary_steam_id: str):
        cypher = """
            MATCH (u:User)
            WHERE u.steamId = $primary_steam_id
            SET u:Primary
            RETURN u AS user
        """
        return tx.run(cypher, primary_steam_id=primary_steam_id).single()

    def set_primary_user(self, primary_steam_id: str) -> dict:
        record = self._write(self.set_primary_user, primary_steam_id=primary_steam_id)
        if not record:
            raise NotFoundException(
                f"Could not find user with steam_id={primary_steam_id}"
            )
        return record["user"]

    @staticmethod
    def _add_friends_tx(tx, steam_id: str, friends: list[dict[str, Any]]):
        cypher = """
            MATCH (u:User {steamId: $steam_id})
            UNWIND $friends AS friend
            MERGE (u)-[:HAS_FRIEND]->(f:User)
            SET f.steamId = friend.steam_id
            SET f.name = friend.name
            RETURN u AS user
        """
        # NOTE: Do not need both directions
        # (use directionless when with MATCH)
        return tx.run(cypher, steam_id=steam_id, friends=friends).single()

    def add_friends(self, steam_id: str, friends: dict[str, Any]) -> dict:
        record = self._write(self._add_friends_tx, steam_id=steam_id, friends=friends)
        if not record:
            raise NotFoundException(f"Could not find user with steam_id={steam_id}")
        return record["user"]
