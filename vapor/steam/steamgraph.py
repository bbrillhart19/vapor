from __future__ import annotations
from typing import Callable
import time
from pathlib import Path

from matplotlib import pyplot as plt
from steam_web_api import Steam
import networkx as nx
from rich.progress import track

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
                    time.sleep(0.1)
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

    def _add_user_node(self, user_id: str) -> None:
        # Already in, don't need to requery
        if user_id in self.adj:
            return

        try:
            user_details = self._query_steam(
                self.steam_client.users.get_user_details, steam_id=user_id
            )["player"]
            name = user_details["personaname"]
        except KeyError:
            print(f"Could not get user details for {user_id}")
            name = user_id
        node_type = "friend" if user_id != self.steam_id else "self"
        self.add_node(user_id, node_type=node_type, name=name)

    def _add_game_node(self, app_id: int) -> None:
        # Already in, don't need to requery
        if app_id in self.adj:
            return

        try:
            app_response = self._query_steam(
                self.steam_client.apps.get_app_details,
                app_id=app_id,
            )
            if not app_response:
                raise KeyError
            app_details = app_response[str(app_id)]
            app_data = app_details["data"]
            app_name = app_data["name"]
        except KeyError:
            # NOTE: Don't use None or there will be downstream issues (i.e. GML save)
            return
        self.add_node(app_id, node_type="game", name=app_name)

    def populate_from_friends(
        self,
        friend_id: str | None = None,
        user_id: str | None = None,
        hops: int = 2,
    ) -> None:
        # TODO: Rework to track connection from previous user to this one and add edge
        # print(user_id, hops)
        # No more hops allowed, skip adding anything from this user
        if hops < 0:
            return
        if not user_id:
            return self.populate_from_friends(None, self.steam_id, hops)

        self._add_user_node(user_id)
        # Add edge from friend id if we have one
        if friend_id:
            self.add_edge(friend_id, user_id)

        # Add games
        games = self._query_steam(
            self.steam_client.users.get_owned_games, steam_id=user_id
        )
        try:
            games_list = games["games"]
        except KeyError:
            print(f"No games found, skipping adding games from {user_id}")
            games_list = []
        for game in track(games_list, description=f"Adding games (user={user_id}):"):
            if "appid" not in game:
                print(f"Skipping a game with no appid from {user_id}")
                continue
            app_id = game["appid"]
            self._add_game_node(app_id)
            if app_id in self:
                self.add_edge(user_id, app_id)

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
        node_types = nx.get_node_attributes(self, "node_type")
        node_type_colors = {
            "self": "red",
            "friend": "green",
            "game": "blue",
        }
        nx.draw_networkx_edges(self, pos=pos)
        nx.draw_networkx_nodes(
            self,
            pos=pos,
            node_color=[node_type_colors[nt] for n, nt in node_types.items()],
        )
        nx.draw_networkx_labels(
            self, pos=pos, labels=nx.get_node_attributes(self, "name"), font_size=6
        )
        plt.show()
