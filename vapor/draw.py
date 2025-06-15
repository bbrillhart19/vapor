from vapor.steam import SteamUserGraph

fp = "./data/steamgraph.gml.gz"

G = SteamUserGraph.load(fp)

user_id = G.steam_id
nodes = [user_id] + [n for n in G.adj[user_id]] + list(G.node_types)
sG = SteamUserGraph(G.subgraph(nodes))
sG.draw()
