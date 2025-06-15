from vapor.steam import SteamUserGraph

fp = "./data/steamgraph.gml.gz"

G = SteamUserGraph.load(fp)

G.extract_subgraph().draw()
