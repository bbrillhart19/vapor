from __future__ import annotations
from typing import Callable, Any, Generator
import time
import warnings

from steam_web_api import Steam

from vapor.utils import utils


class SteamClient(Steam):
    """`Steam` class implemented as it applies to Vapor"""

    def __init__(
        self,
        steam_api_key: str,
        steamid: str,
    ):
        super().__init__(steam_api_key)
        self.steamid = steamid

    @classmethod
    def from_env(cls) -> SteamClient:
        return cls(
            steam_api_key=utils.get_env_var("STEAM_API_KEY"),
            steamid=utils.get_env_var("STEAM_ID"),
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

        if response is None:
            response = {}

        return response

    @staticmethod
    def _extract_fields(response_data: dict, fields: list[str]) -> dict[str, Any]:
        return {field: response_data.get(field) for field in fields}

    def get_user_details(
        self, steamid: str, fields: list[str] = ["steamid"]
    ) -> dict[str, Any]:
        """Query by user id to get details according to `fields`"""
        response = self._query_steam(self.users.get_user_details, steam_id=steamid)
        if not "player" in response:
            warnings.warn(f"Could not get user details for {steamid}")
            return {}
        user_details = response["player"]
        return self._extract_fields(user_details, fields)

    def get_primary_user_details(
        self, fields: list[str] = ["steamid"]
    ) -> dict[str, Any]:
        """Query for the primary user the steam client is based on"""
        return self.get_user_details(self.steamid, fields)

    def get_user_friends(
        self,
        steamid: str,
        fields: list[str] = ["steamid"],
        limit: int | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Get friends list for `steamid` with details specifid by `fields`"""
        # Continue recursively populating from friends list
        friends_response = self._query_steam(
            self.users.get_user_friends_list,
            steam_id=steamid,
            enriched=True,
        )
        if "friends" not in friends_response:
            warnings.warn(f"Could not find friends for user={steamid}")
            friends_list = []
        else:
            friends_list = friends_response["friends"]
        if limit is not None:
            friends_list = friends_list[:limit]
        for friend in friends_list:
            yield self._extract_fields(friend, fields)

    def get_user_owned_games(
        self,
        steamid: str,
        fields: list[str] = ["appid"],
        limit: int | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Get owned games for `steamid` with details specified by `fields`"""
        games_response = self._query_steam(self.users.get_owned_games, steam_id=steamid)
        if "games" not in games_response:
            games_list = []
        else:
            games_list = games_response["games"]
        if limit is not None:
            games_list = games_list[:limit]
        for game in games_list:
            if "appid" not in game:
                continue
            yield self._extract_fields(game, fields)

    def get_game_details(
        self, appid: int, filters: list[str] = ["basic"]
    ) -> dict[str, Any]:
        """Get the genres of a game specified by `appid` and retrieve"""
        response = self._query_steam(
            self.apps.get_app_details, app_id=int(appid), filters=",".join(filters)
        )
        try:
            app_details = response[str(appid)]["data"]
        except KeyError:
            warnings.warn(f"Could not retrieve details for appid={appid}")
            return {}

        return app_details
