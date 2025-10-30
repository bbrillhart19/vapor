import os

import pytest

from steam_web_api import Users, Apps

from vapor.clients import SteamClient
from helpers import globals


def test_steam_from_env(mocker):
    """Tests setting up `SteamClient` from env vars"""
    mocker.patch.dict(os.environ, {"STEAM_API_KEY": "test"})
    mocker.patch.dict(os.environ, {"STEAM_ID": "test"})
    client = SteamClient.from_env()
    assert client.steamid == "test"


@pytest.mark.parametrize(
    "mock_response,expected",
    [
        ({"foo": "bar"}, {"foo": "bar"}),
        (None, {}),
        (Exception("429"), {}),
        (Exception("401"), {}),
        (Exception("500"), {}),
    ],
)
def test_query_steam(mocker, mock_response, expected, steam_client: SteamClient):
    """Tests the steam query wrapper and its ability to handle exceptions"""
    steamid = "test"
    if not isinstance(mock_response, Exception):
        mocker.patch.object(Users, "get_user_details", return_value=mock_response)
    else:
        mocker.patch.object(Users, "get_user_details", side_effect=mock_response)
    response = steam_client._query_steam(
        steam_client.users.get_user_details,
        steamid=steamid,
        retries=1,
        retry_duration=0,
    )
    assert response == expected


def test_extract_fields():
    """Tests the field extraction helper"""
    response = {"foo": "bar"}
    fields = ["foo", "baz"]
    extracted = SteamClient._extract_fields(response, fields)
    for _field in fields:
        if _field in response:
            assert extracted[_field] == response[_field]
        else:
            assert extracted[_field] is None


def test_get_user_details(mocker, steam_client: SteamClient):
    """Tests getting a user's details from their `steamid`"""
    steamid = "test"
    mock_response = {"player": {"steamid": steamid, "foo": "bar"}}
    mocker.patch.object(Users, "get_user_details", return_value=mock_response)
    response = steam_client.get_user_details(steamid)
    assert "steamid" in response
    assert response["steamid"] == steamid
    assert "foo" not in response

    error_response = {"error": "foo"}
    mocker.patch.object(Users, "get_user_details", return_value=error_response)
    response = steam_client.get_user_details(steamid)
    assert response == {}


def test_get_primary_user_details(mocker, steam_client: SteamClient):
    """Tests getting the user details for the primary user"""
    mock_response = {"player": {"steamid": steam_client.steamid, "foo": "bar"}}
    mocker.patch.object(Users, "get_user_details", return_value=mock_response)
    response = steam_client.get_primary_user_details()
    assert response["steamid"] == steam_client.steamid


@pytest.mark.parametrize("limit", [None, 1])
def test_get_user_friends(
    mocker, steam_client: SteamClient, steam_friends: dict[str, list[str]], limit: int
):
    """Tests retrieving a user's friends list"""
    mock_response = {"friends": steam_friends[globals.STEAM_ID]}
    mocker.patch.object(Users, "get_user_friends_list", return_value=mock_response)
    friends = list(steam_client.get_user_friends(globals.STEAM_ID, limit=limit))
    if limit:
        assert len(friends) == limit
    for friend in friends:
        assert "steamid" in friend

    error_response = {"error": "foo"}
    mocker.patch.object(Users, "get_user_friends_list", return_value=error_response)
    friends = list(steam_client.get_user_friends(globals.STEAM_ID, limit=limit))
    assert not friends


@pytest.mark.parametrize(
    "response,limit",
    [
        ({"games": [{"appid": "foo"}]}, None),
        ({"games": [{"appid": "foo"}, {"appid": "bar"}]}, 1),
        ({}, None),
        ({"games": [{"foo": "bar"}]}, None),
    ],
)
def test_parse_games_response(steam_client: SteamClient, response, limit: int):
    """Tests the games response parser helper"""
    games = list(
        steam_client._parse_games_response(games_response=response, limit=limit)
    )
    if limit:
        assert len(games) == limit
    for game in games:
        assert "appid" in game


def test_get_user_owned_games(
    mocker, steam_client: SteamClient, steam_owned_games: dict[str, list[dict]]
):
    """Tests getting the owned games for a user"""
    mock_response = {"games": steam_owned_games[globals.STEAM_ID]}
    mocker.patch.object(Users, "get_owned_games", return_value=mock_response)
    games = list(steam_client.get_user_owned_games(globals.STEAM_ID))
    assert len(games) == len(steam_owned_games[globals.STEAM_ID])
    for game in games:
        assert "appid" in game


def test_get_user_recently_played_games(
    mocker, steam_client: SteamClient, steam_owned_games: dict[str, list[dict]]
):
    """Tests getting the recently played games for a user"""
    mock_response = {"games": steam_owned_games[globals.STEAM_ID]}
    mocker.patch.object(
        Users, "get_user_recently_played_games", return_value=mock_response
    )
    games = list(steam_client.get_user_recently_played_games(globals.STEAM_ID))
    assert len(games) == len(steam_owned_games[globals.STEAM_ID])
    for game in games:
        assert "appid" in game


def test_get_game_details(
    mocker, steam_client: SteamClient, steam_games: dict[int, dict]
):
    """Tests getting the details for a game with an `appid`"""
    appid = 1000
    mock_response = {str(appid): {"data": steam_games[appid]}}
    mocker.patch.object(Apps, "get_app_details", return_value=mock_response)
    response = steam_client.get_game_details(appid)
    assert "name" in response
    assert "genres" in response

    error_response = {"error": "foo"}
    mocker.patch.object(Apps, "get_app_details", return_value=error_response)
    response = steam_client.get_game_details(appid)
    assert response == {}
