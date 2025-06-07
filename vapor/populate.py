from vapor.steam import SteamUserGraph

G = SteamUserGraph()
G.populate_from_friends(max_depth=2)
G.draw()
