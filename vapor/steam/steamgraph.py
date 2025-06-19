from __future__ import annotations
from typing import Callable
import time
from pathlib import Path

from matplotlib import pyplot as plt
from steam_web_api import Steam
import networkx as nx
from rich.progress import track
from html2text import HTML2Text

from vapor.utils import utils


class SteamUserGraph(nx.Graph):
    def __init__(
        self,
        incoming_graph_data=None,
        steam_api_key: str | None = None,
        steam_id: str | None = None,
    ):
        super().__init__(incoming_graph_data=incoming_graph_data)
        self.steam_api_key = utils.get_env_var("STEAM_API_KEY", steam_api_key)
        self.steam_id = utils.get_env_var("STEAM_ID", steam_id)
        self.steam_client = Steam(self.steam_api_key)
        self._add_node_types()
        self.html_parser = self._setup_html_parser()

    @property
    def node_types(self) -> set:
        return {"self", "user", "game"}

    def _add_node_types(self) -> None:
        for nt in self.node_types:
            self.add_node(nt, name=nt)

    def _get_node_type(self, node: str) -> str:
        if node in self.node_types:
            return node
        for nt in self.node_types:
            if node in self.adj[nt]:
                return nt
        raise IndexError(f"{node} not found in any node type")

    def _validate_node_type(self, node_type: str) -> str:
        if node_type not in self.node_types:
            raise ValueError(f"Got invalid node_type={node_type}")
        return node_type

    def _is_node_type(self, node: str, node_type: str) -> bool:
        return self._get_node_type(node) == self._validate_node_type(node_type)

    def is_game(self, node: str) -> bool:
        return self._is_node_type(node, "game")

    def is_user(self, node: str) -> bool:
        return self._is_node_type(node, "user")

    def is_self(self, node: str) -> bool:
        return self._is_node_type(node, "self")

    @property
    def games(self) -> dict[str, str]:
        return nx.get_node_attributes(self.subgraph(self.adj["games"]), "name")

    @property
    def users(self) -> dict[str, str]:
        # user_nodes = [n for n in self.adj["user"]]
        return nx.get_node_attributes(self.subgraph(self.adj["user"]), "name")

    @staticmethod
    def _setup_html_parser() -> HTML2Text:
        h = HTML2Text()
        h.ignore_links = True
        h.ignore_emphasis = True
        h.ignore_images = True
        return h

    def save(self, filepath: Path | str) -> None:
        filepath = utils.cast_path(filepath)
        utils.create_dir(filepath.parent)
        nx.write_gml(self, filepath)

    @classmethod
    def load(cls, filepath: Path | str, **kwargs) -> SteamUserGraph:
        G = nx.read_gml(filepath)
        return cls(incoming_graph_data=G, **kwargs)

    def _query_steam(
        self, query_func: Callable[..., dict], retries: int = 5, **kwargs
    ) -> dict:
        # Exception: 429 Too Many Requests
        # Exception: 401 Unauthorized {}
        response = {}
        try:
            response = query_func(**kwargs)
        except Exception as e:
            # Too many requests, sleep and retry
            if e.args[0].startswith("429"):
                if retries > 0:
                    print(f"Too many requests, retrying (remaining: {retries})...")
                    time.sleep(0.2)
                    return self._query_steam(query_func, retries=retries - 1, **kwargs)
                else:
                    print(
                        f"Reached maximum retries, cannot complete query. Try again later!"
                    )
            elif e.args[0].startswith("401"):
                print(f"Query unauthorized, skipping!")
            else:
                print(f"Caught an unhandled query exception:\n{e}")

        return response

    def _add_user_node(self, user_id: str, from_user_id: str | None = None) -> None:
        # Don't requery if already in graph
        if user_id not in self:
            try:
                user_details = self._query_steam(
                    self.steam_client.users.get_user_details, steam_id=user_id
                )["player"]
                name = user_details["personaname"]
            except KeyError:
                print(f"Could not get user details for {user_id}")
                name = user_id
            # Add user node with personaname
            self.add_node(user_id, name=name)
            # Add additional to connection to self if matched steam_id
            if user_id == self.steam_id:
                self.add_edge(user_id, "self")
            # Otherwise add connection to user node type
            else:
                self.add_edge(user_id, "user")

        # Add edge from friend id if we have one
        if from_user_id:
            self.add_edge(user_id, from_user_id)

    def _add_game_node(
        self, response_data: dict, from_user_id: str | None = None
    ) -> None:
        if "appid" not in response_data:
            return
        else:
            app_id = str(response_data["appid"])
        if "name" not in response_data:
            return
        else:
            app_name = response_data["name"]
        # Can set these regardless if game is already present
        self.add_node(app_id, name=app_name)
        self.add_edge(app_id, "game")

        if from_user_id:
            self.add_edge(from_user_id, app_id)

    def _add_user_games_list_nodes(self, user_id: str) -> None:
        # Add games from the user's games list
        games = self._query_steam(
            self.steam_client.users.get_owned_games, steam_id=user_id
        )
        if "games" not in games:
            print(f"Could not add games for user={user_id}")
            return
        for game in track(games["games"], description=f"Adding games (user={user_id})"):
            self._add_game_node(game, user_id)

    def populate_from_friends(
        self, friend_id: str | None = None, user_id: str | None = None, hops: int = 2,
    ) -> None:
        # No more hops allowed, skip adding anything from this user
        if hops < 0:
            return
        if not user_id:
            return self.populate_from_friends(None, self.steam_id, hops)
        # Add the user
        self._add_user_node(user_id, friend_id)
        # Add the user's games
        self._add_user_games_list_nodes(user_id)

        # Continue recursively populating from friends list
        friends = self._query_steam(
            self.steam_client.users.get_user_friends_list,
            steam_id=user_id,
            enriched=False,
        )
        try:
            friends_list = friends["friends"]
        except KeyError:
            print(f"No friends found, skipping adding friends from {user_id}")
            friends_list = []
        for friend in friends_list:
            # NOTE: Something would be very wrong if the friend doesn't have a steamid
            self.populate_from_friends(user_id, friend["steamid"], hops - 1)

    def draw(self) -> None:
        pos = nx.spring_layout(self)
        node_type_colors = {
            "self": "red",
            "user": "green",
            "game": "blue",
        }
        node_colors = [node_type_colors[self._get_node_type(n)] for n in self.nodes]
        nx.draw_networkx_edges(self, pos=pos)
        nx.draw_networkx_nodes(
            self, pos=pos, node_color=node_colors,
        )
        nx.draw_networkx_labels(
            self, pos=pos, labels=nx.get_node_attributes(self, "name"), font_size=6
        )
        plt.show()

    def extract_subgraph(self, node: str | None = None) -> SteamUserGraph | None:
        # Extract the subgraph (+node types) for the node
        if not node:
            node = self.steam_id
        if node not in self:
            print(f"Node={node} not found.")
            return None

        nodes = {node}
        for n in self.adj[node]:
            nodes.add(n)
            nodes.add(self._get_node_type(n))
        return SteamUserGraph(self.subgraph(nodes))

    def about_the_game(self, app_id: str) -> tuple[str, str]:
        app_details = self._query_steam(
            self.steam_client.apps.get_app_details, app_id=int(app_id)
        )

        try:
            game_doc_html = app_details[app_id]["data"]["about_the_game"]
        except KeyError:
            print(f"Could not retrieve game details for app_id={app_id}")
            game_doc_html = ""

        game_doc = self.html_parser.handle(game_doc_html)

        try:
            app_name = app_details[app_id]["data"]["name"]
        except KeyError:
            print(f"Could not retrieve name for app_id={app_id}")
            app_name = app_id

        return app_name, game_doc
