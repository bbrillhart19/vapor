from pathlib import Path

from vapor.steam import SteamUserGraph
from vapor.utils import utils


graph_file = utils.default_nx_graph_file()
G = SteamUserGraph()
G.populate_from_friends(hops=1)
G.save(graph_file)

print(f"Graph population complete, saved to {graph_file}")
print("Stats:")
for nt in G.node_types:
    print(nt, len(G.adj[nt]))
