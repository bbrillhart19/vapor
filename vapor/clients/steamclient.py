from __future__ import annotations
from typing import Callable, Any, Generator
import time

from loguru import logger
from steam_web_api import Steam
from html2text import HTML2Text

from vapor.utils import utils


class SteamClient(Steam):
    """`steam_web_api.Steam` class implemented for use with Vapor"""

    def __init__(
        self,
        steam_api_key: str,
        steamid: str,
    ):
        super().__init__(steam_api_key)
        self.steamid = steamid
        self.html_parser = self._setup_html_parser()

    @classmethod
    def from_env(cls) -> SteamClient:
        return cls(
            steam_api_key=utils.get_env_var("STEAM_API_KEY"),
            steamid=utils.get_env_var("STEAM_ID"),
        )

    @staticmethod
    def _setup_html_parser() -> HTML2Text:
        h = HTML2Text()
        h.ignore_links = True
        h.ignore_emphasis = True
        h.ignore_images = True
        h.body_width = 0
        return h

    def _query_steam(
        self,
        query_func: Callable[..., dict],
        retries: int = 5,
        retry_duration: float = 0.2,
        **kwargs,
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
                    logger.warning(
                        f"Too many requests, retrying (remaining: {retries})..."
                    )
                    time.sleep(retry_duration)
                    return self._query_steam(query_func, retries=retries - 1, **kwargs)
                else:
                    logger.error(
                        f"Reached maximum retries, cannot complete query. Try again later!"
                    )
            # TODO: Need to provide information back to caller for caller to handle
            # and potentially provide more info
            elif e.args[0].startswith("401"):
                logger.error(f"Query unauthorized, skipping!")
            else:
                logger.error(f"Caught an unhandled query exception:\n{e}")

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
            # NOTE: Silently ignoring these misses for now to avoid
            # flooding console
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
            # NOTE: Silently ignoring these misses for now to avoid
            # flooding console
            friends_list = []
        else:
            friends_list = friends_response["friends"]
        if limit is not None:
            friends_list = friends_list[:limit]
        for friend in friends_list:
            yield self._extract_fields(friend, fields)

    def _parse_games_response(
        self,
        games_response: Any,
        fields: list[str] = ["appid"],
        limit: int | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Parses the raw `games_response` and extracts the `fields`
        and their values up to `limit` total games.
        """
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

    def get_user_owned_games(
        self,
        steamid: str,
        fields: list[str] = ["appid"],
        limit: int | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Get owned games for `steamid` with details specified by `fields`."""
        games_response = self._query_steam(self.users.get_owned_games, steam_id=steamid)
        return self._parse_games_response(games_response, fields=fields, limit=limit)

    def get_user_recently_played_games(
        self, steamid: str, fields: list[str] = ["appid"], limit: int | None = None
    ):
        """Get recently played games, the results of which should
        already have their details defined by `get_user_owned_games`.
        """
        games_response = self._query_steam(
            self.users.get_user_recently_played_games, steam_id=steamid
        )
        return self._parse_games_response(games_response, fields=fields, limit=limit)

    def get_game_details(
        self, appid: int, filters: list[str] = ["basic"]
    ) -> dict[str, Any]:
        """Get the details of a game with `appid` applied to the
        returned fields specified by `filters`.
        NOTE: The 'basic' filter includes several fields that can only
        be retrieved by using the 'basic' filter and getting all of them.
        Other fields, such as 'genres', are optional and can be specified
        individually.
        """
        response = self._query_steam(
            self.apps.get_app_details, app_id=int(appid), filters=",".join(filters)
        )
        try:
            app_details = response[str(appid)]["data"]
        except KeyError:
            # NOTE: Silently ignoring these misses for now to avoid
            # flooding console
            return {}

        return app_details

    def get_game_genres(self, appid: int) -> list[dict[str, Any]]:
        """Retrieve the genres for the game with `appid`."""
        # Get game details with 'genres' filter
        game_details = self.get_game_details(appid, filters=["genres"])
        if "genres" not in game_details:
            return []
        return game_details["genres"]

    def about_the_game(self, appid: int) -> str | None:
        """Get the `'about_the_game'` description for the game with `appid`."""
        # Get game details with 'basic' filter (which includes 'about_the_game')
        game_details = self.get_game_details(appid, filters=["basic"])
        if "about_the_game" not in game_details:
            return None

        # Get the HTML game description
        game_doc_html = game_details["about_the_game"]
        game_doc = self.html_parser.handle(game_doc_html)
        return game_doc
