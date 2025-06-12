from vapor.steam import SteamUserGraph

fp = "./data/steamgraph.gml.gz"

G = SteamUserGraph()
G.populate_from_friends(hops=1)


G.save(fp)

G_in = SteamUserGraph.load(fp)
G_in.draw()
