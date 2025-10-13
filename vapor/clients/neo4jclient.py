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

    def _read(self, cypher: str, limit: int | None = None, **kwargs) -> pd.DataFrame:
        """Run the `cypher` query in 'read' mode, always transforming
        and returning the results as a dataframe. If `limit` is supplied,
        only that amount of items will be returned.
        """
        if limit:
            cypher += f" LIMIT {limit}"
        return self.driver.execute_query(
            cypher,
            database_=self._database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda r: r.to_df(),
            **kwargs,
        )

    def _set_node_constraint(
        self, constraint_name: str, node_label: str, node_property: str
    ) -> None:
        cypher = """
            CREATE CONSTRAINT {0} IF NOT EXISTS FOR (n:{1}) REQUIRE (n.{2}) IS UNIQUE
        """.format(
            constraint_name, node_label, node_property
        )
        self._write(cypher)

    def _set_user_constraint(self) -> None:
        self._set_node_constraint("user_constraint", "User", "steamId")

    def _set_game_constraint(self) -> None:
        self._set_node_constraint("game_constraint", "Game", "appId")

    def _set_genre_constraint(self) -> None:
        self._set_node_constraint("genre_constraint", "Genre", "genreId")

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

        Returns:
            dict[str, Any]: The primary user info from the primary node.

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
        required_constraints = {
            "game_constraint",
            "user_constraint",
            "genre_constraint",
        }
        constraints = set(self._get_constraints()["name"])
        missing_constraints = required_constraints - constraints
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
        self._set_genre_constraint()

        # Recurse to validate success
        self.setup_from_primary_user(**primary_user)

    @staticmethod
    def _validate_node_fields(
        nodes: list[dict[str, Any]], defaults: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Validates a set of `nodes` to be inserted to the graph
        and returns the validated set, skipping any nodes that are
        missing required fields, which are indicated in the `defaults`
        list as `"field": None`. If a field is optional and missing from
        a `node`, it will use the value from the `defaults`. Only the
        fields that are in the `defaults` mapping will be included in
        the returned validated nodes.

        Args:
            nodes (list[dict[str, Any]]): The input node messages
                to be validated.
            defaults (dict[str, Any]): The default mapping of fields
                and their values. Indicate required fields by setting
                their values as `None`.

        Returns:
            list[dict[str, Any]]: _description_
        """
        validated_nodes: list[dict[str, Any]] = []
        for node in nodes:
            validated_node = {}
            valid = True
            for field, val in defaults.items():
                # Expected field is missing from node
                if field not in node or node[field] is None:
                    # Required field missing, skip this node
                    if val is None:
                        valid = False
                        break
                    # Not a required field, set default
                    validated_node[field] = val
                    continue
                # Expected field is in node with value, set it as is
                validated_node[field] = node[field]
            # Add to validated_nodes if validated
            if valid:
                validated_nodes.append(validated_node)
        return validated_nodes

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
        validated_friends = self._validate_node_fields(
            nodes=friends,
            defaults={
                "steamid": None,
                "personaname": "Unavailable",
            },
        )
        cypher = """
            MATCH (u:User {steamId: $steamid})
            UNWIND $friends AS friend
            MERGE (f:User {steamId: friend.steamid, personaName: friend.personaname})
            MERGE (u)-[:HAS_FRIEND]-(f)
        """
        self._write(cypher, steamid=steamid, friends=validated_friends)

    def get_all_users(self, limit: int | None = None) -> pd.DataFrame:
        """Retrieve all `User` nodes from the database.

        Args:
            limit (int, optional): Limits the amount of users returned.
                If None, all users in the graph are returned.
                Defaults to None.

        Returns:
            pd.DataFrame: All `User` nodes from database and their
                node properties as a `DataFrame` object.
        """
        cypher = """
            MATCH (u:User)
            RETURN u.steamId as steamid, u.personaName as personaname
        """
        return self._read(cypher, limit)

    def add_owned_games(self, steamid: str, games: list[dict[str, Any]]) -> None:
        """Add the list of `games` as `Game` nodes which are owned by
        the `User` node matching `steamid`.

        Args:
            steamid (str): The Steam user ID of the user to add `games`
                relationships to.
            games (list[dict[str, Any]]): The list of games each with
                parameters of `appid` and `name`.
        """
        validated_games = self._validate_node_fields(
            nodes=games,
            defaults={
                "appid": None,
                "name": None,
                "playtime_forever": 0,
            },
        )
        cypher = """
            MATCH (u:User {steamId: $steamid})
            UNWIND $games AS game
            MERGE (g:Game {appId: game.appid, name: game.name})
            MERGE (u)-[:OWNS_GAME {
                playtime: game.playtime_forever
            }]->(g)
        """
        self._write(cypher, steamid=steamid, games=validated_games)

    def get_owned_games(self, steamid: str, limit: int | None = None) -> pd.DataFrame:
        """Retrieve all owned games up to `limit` for the User node matching `steamid`

        Args:
            steamid (str): The Steam user ID of the user to get owned games for.

        Returns:
            pd.DataFrame: All `Game` nodes owned by the user.
        """
        cypher = """
            MATCH (u: {steamId: $steamid})
            MATCH (u)-[:OWNS_GAME]->(g:Game)
            RETURN g.appId as appid, g.name as name
        """
        return self._read(cypher, limit, steamid=steamid)

    def get_all_games(self, limit: int | None = None) -> pd.DataFrame:
        """Retrieve all `Game` nodes from the database.

        Args:
            limit (int, optional): Limits the amount of users returned.
                If None, all users in the graph are returned.
                Defaults to None.

        Returns:
            pd.DataFrame: All `Game` nodes from database and their
                node properties as a `DataFrame` object.
        """
        cypher = """
            MATCH (g:Game)
            RETURN g.appId as appid, g.name as name
        """
        return self._read(cypher, limit)

    def add_game_genres(self, appid: int, genres: list[dict[str, Any]]) -> None:
        """Add the list of `genres` as `Genre` nodes for the game
        matching the provided `appid`.

        Args:
            appid (int): The Steam app id number of the game
                to add the `genres` relationships to.
            genres (list[dict[str, Any]]): The genres the game
                is a member of, including properties of
        """
        validated_genres = self._validate_node_fields(
            nodes=genres,
            defaults={
                "id": None,
                "description": None,
            },
        )
        cypher = """
            MATCH (g:Game {appId: $appid})
            UNWIND $genres as genre
            MERGE (n:Genre {genreId: toInteger(genre.id), description: genre.description})
            MERGE (g)-[:HAS_GENRE]->(n)
        """
        self._write(cypher, appid=appid, genres=validated_genres)

    def update_recently_played_games(
        self, steamid: str, games: list[dict[str, Any]]
    ) -> None:
        """Update the recently played games for the user with `steamid`
        by adding an additional relationship for the `User` node to
        each of the `Game` nodes. Any games that are no longer members
        of the recently played list will have that relationship removed
        from the user.

        Args:
            steamid (str): The Steam user ID of the user to add `games`
                with `RECENTLY_PLAYED` relationship to.
            games (list[dict[str, Any]]): The list of games each with
                at least the parameter of `appid`.
        """
        # First query removes all recently played relationships
        delete_cypher = """
            MATCH (u:User {steamId: $steamid})
            MATCH (u)-[r:RECENTLY_PLAYED]->()            
            DELETE r
        """
        self._write(delete_cypher, steamid=steamid)
        # Validate the game nodes
        validated_games = self._validate_node_fields(
            nodes=games, defaults={"appid": None, "playtime_2weeks": 0}
        )
        # Second query adds recently played relationships from the updated list
        update_cypher = """
            MATCH (u:User {steamId: $steamid})
            UNWIND $games as game 
            MATCH (g:Game {appId: game.appid})  
            MERGE (u)-[:RECENTLY_PLAYED {
                recentPlaytime: game.playtime_2weeks
            }]->(g)
        """
        return self._write(update_cypher, steamid=steamid, games=validated_games)

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
