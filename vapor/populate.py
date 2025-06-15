from vapor.steam import SteamUserGraph

fp = "./data/steamgraph.gml.gz"

G = SteamUserGraph()
G.populate_from_friends(hops=1)
G.save(fp)

print(f"Graph population complete, saved to {fp}")
print("Stats:")
for nt in G.node_types:
    print(nt, len(G.adj[nt]))
