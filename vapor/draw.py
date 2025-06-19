from vapor.steam import SteamUserGraph
from vapor.utils import utils

fp = utils.default_nx_graph_file()
G = SteamUserGraph.load(fp)

savefn = fp.parent.joinpath(f"{G.steam_id}_subgraph.png")
G.extract_subgraph().draw(savefn)
