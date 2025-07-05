from __future__ import annotations
from typing import Callable, Any, Generator
import time

from steam_web_api import Steam

from vapor.utils import utils


class SteamClient(Steam):
    """`Steam` class implemented as it applies to Vapor"""

    def __init__(
        self, steam_api_key: str, steam_id: str,
    ):
        super().__init__(steam_api_key)
        self.steam_id = steam_id

    @classmethod
    def from_env(cls) -> SteamClient:
        return cls(
            steam_api_key=utils.get_env_var("STEAM_API_KEY"),
            steam_id=utils.get_env_var("STEAM_ID"),
        )

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

    @staticmethod
    def _extract_fields(response_data: dict, fields: list[str]) -> dict[str, Any]:
        return {field: response_data.get(field) for field in fields}

    def get_user_details(
        self, user_id: str, fields: list[str] = ["steam_id"]
    ) -> dict[str, Any]:
        """Query by user id to get details according to `fields`"""
        response = self._query_steam(self.users.get_user_details, steam_id=user_id)
        if not "player" in response:
            print(f"Could not get user details for {user_id}")
            return {}
        user_details = response["player"]
        return self._extract_fields(user_details, fields)

    def get_primary_user_details(
        self, fields: list[str] = ["steam_id"]
    ) -> dict[str, Any]:
        """Query for the primary user the steam client is based on"""
        return self.get_user_details(self.steam_id, fields)

    def get_user_owned_games(
        self, user_id: str, fields: list[str] = ["appid"]
    ) -> Generator[dict[str, Any], None, None]:
        """Get owned games for `user_id` with details specified by `fields`"""
        games = self._query_steam(self.users.get_owned_games, steam_id=user_id)
        if "games" not in games:
            print(f"Could not find owned games for user={user_id}")
            games["games"] = []

        for game in games["games"]:
            game_details = {}
            if "appid" not in game:
                continue
            yield self._extract_fields(game_details, fields)

    def get_user_friends(
        self, user_id: str, fields: list[str] = ["steam_id"]
    ) -> list[dict[str, Any]]:
        """Get friends list for `user_id` with details specifid by `fields`"""
        # Continue recursively populating from friends list
        friends = self._query_steam(
            self.users.get_user_friends_list, steam_id=user_id, enriched=True,
        )
        if "friends" not in friends:
            print(f"Could not find friends for user={user_id}")
            friends["friends"] = []
        detailed_friends_list = [
            self._extract_fields(friend, fields) for friend in friends["friends"]
        ]
        return detailed_friends_list
