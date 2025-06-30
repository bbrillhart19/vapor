Vapor
-------

Doing stuff with Steam. Don't know what yet.

## Getting Started
Currently, the application is not published anywhere and must be built from source, thus you must first clone the repository to the system you'd like to run `vapor` on.

### Setup Environment
A few environment variables need to be acquired and set for your personal use. Copy the `.env.example` file like this so you can customize it for yourself:
```shell
cp .env.example .env
```
And edit the `.env` file with the required values using the comments for each as a reference. You will need to acquire a Steam Web API Key [here](https://steamcommunity.com/dev).

### Docker Installation
This application requires Docker to run, whether you are a user or developing the codebase. Install Docker depending on your OS:

#### Windows/Mac
Install Docker Desktop [for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) or [for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)

#### WSL/Linux
Install Docker via the CLI:
```shell
sudo apt-get update && sudo apt-get install docker.io docker-compose-v2
```

## Usage
Currently, this program simply queries the Steam Web API to find games that you and your friends (and your friends' friends, and...) are playing and creates the resulting graph.

### Start Neo4j
[Neo4j](https://neo4j.com/) is a GraphDB which is used by `vapor` to store your interactions with different games and users. Before doing anything else, spin up the `neo4j` server with:
```shell
docker compose up -d
```
If all went well, you should be able to navigate to `http://localhost:7474` in your browser and view the `noe4j` database. If you know the [Cypher query language](https://neo4j.com/docs/cypher-manual/current/introduction/) this is where you can write queries to view parts of your "Vapor Graph" once it is [populated](#graph-population).

------
***NOTE: Everything below this^ line will be changed following `neo4j` integration***
### Graph Population
To create your `SteamUserGraph` and store it to your `VAPOR_DATA_PATH`, run:
```bash
docker compose run --rm vapor python vapor/populate.py
```
Example output (shortened):
```text
### Adding games... ###
Graph population complete, saved to ./data/steamgraph.gml.gz
Stats:
game 1242
self 1
user 11
```

### Graph Display
To save a plot to your `VAPOR_DATA_PATH` of your "subgraph", which is only your immediate friends and games:
```bash
docker compose run --rm python vapor/draw.py
```
![subgraph](docs/images/subgraph.png)

### Game Info
To retrieve a game description along with information about who in your `SteamUserGraph` plays the game:
```bash
docker compose run --rm vapor python vapor/info.py -a <app_id>
# Example - Stardew Valley:
docker compose run --rm vapor python vapor/info.py -a 413150
```
Example output (shortened):
```text
<<< Game info for app_id=413150 >>>

========== Stardew Valley ==========

Stardew Valley is an open-ended country-life RPG!
### More info...###

========== Graph Info ==========

You do not play this game.
7 user(s) related to you play this game:
["Endor's Game", 'Chasm', 'JFKShotFirst', 'MistaHiggins', 'KJos', 'emily.puls0828', 'The Great Jumanji']
```

## Development
Refer to this section only if you are developing the codebase. 

### Requirements
- Python
- Pip

### Installation
Install the editable `dev` package, preferably within a virtual environment, with:
```shell
pip install -e .[dev]
```

### Development Checklist
- [ ] Ensure [environment](#installation) is setup and activated
- [ ] Make code changes with proper [formatting](#code-formatting)
- [ ] Locally, ensure passing [unit tests](#unit-tests)
- [ ] Additionally run necessary [integration tests](#integration-tests)
- [ ] TODO: CI/CD with Actions

#### Code Formatting
This codebase is formatted using `black`. Prior to pushing any changes/commits, format them with:
```shell
black vapor
```

#### Unit Tests
TODO - `pytest`

#### Integration Tests
TODO - Locally run with Docker 
