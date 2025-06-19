from vapor.steam import SteamUserGraph
from vapor.utils import utils


def info(app_id: str) -> None:
    fp = utils.default_nx_graph_file()
    G = SteamUserGraph.load(fp)

    print(f"<<< Game info for app_id={app_id} >>>")
    app_name, game_doc = G.about_the_game(app_id)
    print(f"\n{'='*10} {app_name} {'='*10}\n")
    print(game_doc)

    sG = G.extract_subgraph(app_id)
    if isinstance(sG, SteamUserGraph):
        print(f"\n{'='*10} Graph Info {'='*10}\n")
        if G.steam_id in sG.adj["self"]:
            print("You play this game.")
        else:
            print("You do not play this game.")
        print(f"{len(sG.users)} user(s) related to you play this game:")
        print([name for _, name in sG.users.items()])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Retrieve info about a game")
    parser.add_argument(
        "-a",
        "--app-id",
        type=str,
        help="The app ID of the game to get info for.",
        required=True,
    )
    args = parser.parse_args()
    info(**args.__dict__)
