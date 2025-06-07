import os

import chromadb
from steam_web_api import Steam
from html2text import HTML2Text

chroma_client = chromadb.EphemeralClient()
print(chroma_client.list_collections())
collection = chroma_client.create_collection("test")
print(chroma_client.list_collections())
steam_client = Steam(os.getenv("STEAM_API_KEY", ""))
h = HTML2Text()
h.ignore_links = True
h.ignore_emphasis = True
h.ignore_images = True
friends_list = steam_client.users.get_user_friends_list(os.getenv("STEAM_ID", ""))
owned_games = steam_client.users.get_owned_games(os.getenv("STEAM_ID", ""))

documents = []
app_ids = []
for game in owned_games["games"]:
    app_details = steam_client.apps.get_app_details(game["appid"])
    # print(h.handle(app_details[str(game["appid"])]["data"]["about_the_game"]))
    # print("="*20)
    game_doc = h.handle(app_details[str(game["appid"])]["data"]["about_the_game"])
    app_ids.append(str(game["appid"]) + f"-{game['name']}")
    documents.append(game_doc)

collection.add(documents=documents, ids=app_ids)


results = collection.query(
    query_texts=["A really cool space game"], include=["distances"]
)

print(results)
