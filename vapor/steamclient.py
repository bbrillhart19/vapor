"""References:
https://developer.valvesoftware.com/wiki/Steam_Web_API
https://api.steampowered.com/ISteamWebAPIUtil/GetSupportedAPIList/v0001/
https://github.com/deivit24/python-steam-api
"""

import os
import json

from steam_web_api import Steam

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

if not STEAM_API_KEY:
    raise ValueError("STEAM_API_KEY is not set!")

steam = Steam(STEAM_API_KEY)

response = steam.apps.search_games("helldivers 2")
app_id = response["apps"][0]["id"][0]
response = steam.apps.get_app_details(app_id)
print(response[str(app_id)]["data"].keys())
# print(response[str(app_id)]["data"]["about_the_game"])
