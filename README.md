Vapor
-------

Doing stuff with Steam. Don't know what yet.

## Getting Started

### Requirements
- Python >= 3.9
- Pip

### Installation
Install the package for development with:
```bash
$ pip install -e .[dev]
```

### Environment Variables
You'll need to obtain certain API keys and set the following environment variables:

#### Steam
Acquire a Steam Web API Key [here](https://steamcommunity.com/dev) (use `localhost` for the domain name) and set the following environment variable:
```bash
$ export STEAM_API_KEY="<your api key>"
```
Also, get your Steam ID (the actual ID number, not your username) and set this:
```bash
$ export STEAM_ID="<your steam id>"
```

## Usage
Currently, this program simply queries the Steam Web API to find games that you and your friends (and your friends' friends, and...) are playing and creates the resulting graph.

### Graph Population
To create your `SteamUserGraph` and store it, run:
```bash
$ python vapor/populate.py
### Adding games... ###
Graph population complete, saved to ./data/steamgraph.gml.gz
Stats:
game 1242
self 1
user 11
```

### Graph Display
To display your "subgraph", which is only your friends and the games you have in common:
```bash
$ python vapor/draw.py
```
![subgraph](docs/images/subgraph.png)

### Game Info
To retrieve a game description along with information about who in your `SteamUserGraph` plays the game:
```bash
$ python vapor/info.py -a <app_id>
# Example - Stardew Valley:
$ python vapor/info.py -a 413150
<<< Game info for app_id=413150 >>>

========== Stardew Valley ==========

Stardew Valley is an open-ended country-life RPG!
### More info...###

========== Graph Info ==========

You do not play this game.
7 user(s) related to you play this game:
["Endor's Game", 'Chasm', 'JFKShotFirst', 'MistaHiggins', 'KJos', 'emily.puls0828', 'The Great Jumanji']
```
