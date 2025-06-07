import os

from matplotlib import pyplot as plt
from steam_web_api import Steam
import networkx as nx

from vapor.utils import env


class SteamUserGraph(nx.Graph):
    def __init__(self, steam_api_key: str | None = None, steam_id: str | None = None):
        super().__init__()
        self.steam_api_key = env.get_env_var("STEAM_API_KEY", steam_api_key)
        self.steam_id = env.get_env_var("STEAM_ID", steam_id)
        self.steam_client = Steam(self.steam_api_key)

    def populate_from_friends(
        self, user_id: str | None = None, depth: int = 0, max_depth: int = 2
    ) -> None:
        # TODO: Rework to track connection from previous user to this one and add edge
        print(user_id, depth)
        if depth == max_depth:
            return
        if not user_id:
            return self.populate_from_friends(self.steam_id, 0, max_depth)

        try:
            games = self.steam_client.users.get_owned_games(user_id)
        except Exception:
            print(f"Got error populating games list from {user_id}, skipping >>>")
            return

        try:
            friends = self.steam_client.users.get_user_friends_list(
                user_id, enriched=False
            )
        except Exception:
            print(f"Got error populating friends list from {user_id}, skipping >>>")
            return

        # TODO: Move this to add user node
        user_details = self.steam_client.users.get_user_details(user_id)["player"]
        node_type = "friend" if user_id != self.steam_id else "self"
        self.add_node(user_id, node_type=node_type, name=user_details["personaname"])

        for game in games["games"]:
            # TODO: Move this to add game node
            app_id = game["appid"]
            app_details = self.steam_client.apps.get_app_details(app_id)[str(app_id)]
            if "data" not in app_details:
                print(f"Could not get app details for {app_id}, skipping >>>")
                continue
            app_name = app_details["data"]["name"]
            self.add_node(app_id, node_type="game", name=app_name)
            self.add_edge(user_id, app_id)

        for friend in friends["friends"]:
            friend_id = friend["steamid"]
            self.add_edge(user_id, friend_id)
            self.populate_from_friends(friend["steamid"], depth + 1, max_depth)

    def draw(self) -> None:
        pos = nx.spring_layout(self)
        nx.draw(self, pos=pos)
        nx.draw_networkx_labels(
            self, pos=pos, labels=nx.get_node_attributes(self, "name"), font_size=6
        )
        plt.show()
