<h1 align="center">Vapor</h1>
<p align="center">
    <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff"></a>
    <a href="https://www.docker.com/"><img alt="Docker" src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff"></a>
    <a href="https://neo4j.com/"><img alt="Neo4j" src="https://img.shields.io/badge/Neo4j-008CC1?logo=neo4j&logoColor=white"></a>
    <a href="https://store.steampowered.com/"><img alt="Steam" src="https://img.shields.io/badge/Steam-%23000000.svg?logo=steam&logoColor=white"></a>
    <a href="https://docs.langchain.com/"><img alt="LangChain" src="https://img.shields.io/badge/LangChain-1c3c3c.svg?logo=langchain&logoColor=white"></a>
    <a href="https://docs.ollama.com/"><img alt="Ollama" src="https://img.shields.io/badge/Ollama-fff?logo=ollama&logoColor=000"></a>
    <a href="https://gofastmcp.com/getting-started/welcome"><img alt="FastMCP" src=https://img.shields.io/badge/MCP-FastMCP_2.x-blue></a>
</p>
<p align="center">
    <a href="https://github.com/bbrillhart19/vapor/actions/workflows/test.yml?query=branch:main"><img alt="Build status" src="https://img.shields.io/github/actions/workflow/status/bbrillhart19/vapor/test.yml?branch=main"></a>
    <a href="https://github.com/bbrillhart19/vapor/actions/workflows/test.yml?query=branch:main"><img alt="Coverage" src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/bbrillhart19/6914181b8919f158adf1aeaca40bea63/raw/vapor-coverage.json"></a>
    <a href="https://github.com/bbrillhart19/vapor/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/bbrillhart19/vapor.svg"></a>
</p>


## About
A personalized AI chat companion for gamers built on Steam data and GraphRAG.

## Getting Started
Before proceeding, clone the repository to your system.

### Requirements
- Python
- Pip
- [Docker](#docker-installation)

### Installation
Install the editable `vapor` package, preferably within a virtual environment, with:
```shell
pip install -e .[core]
```

### Setup Environment
A few environment variables need to be acquired and set for your personal use. First, create your environment from the example using the convenience script:
```shell
bash scripts/update-env.sh

Created .env from .env.example
⚠️  The following preserved keys were not set in your previous .env:
   - STEAM_API_KEY
   - STEAM_ID
   - OLLAMA_API_KEY
   You must update them before proceeding further.
✅ .env reset from .env.example with preserved values applied
```
Edit the `.env` file with the required values (see the warnings about "preserved keys") using the comments for each as a reference. You will need to acquire the following keys:
  - Steam Web API Key [here](https://steamcommunity.com/dev).
  - Create an account at [Ollama](https://docs.ollama.com/) and generate an API key [here](https://ollama.com/settings/keys).

**NOTE:** When the `.env.example` adds/removes variables, you will need to reflect these changes in your own `.env`. You can do this by simply re-running the `update-env.sh` script, which will preserve any keys in the `.env.example` marked as `# preserved` (i.e. API keys) and add/remove anything else to stay in step with the current required environment.

**NOTE:** You can set a custom path to environment if you wish with:
```shell
export VAPOR_ENV=path/to/your.env
```

### Docker Installation
This application requires Docker to run, whether you are a user or developing the codebase. Install Docker depending on your OS and take additional steps depending on if you have an NVIDIA GPU available.

**NOTE:** It is not advisable to attempt to setup Vapor on a device w/o an NVIDIA GPU. It is doable, however, be aware that processes requiring local model inference (ex: embeddings for vector search) will be quite slow. For [developers](#development), however, GPU resources are not necessary.

#### WSL/Linux
Install Docker via the CLI:
```shell
sudo apt-get update && sudo apt-get install docker.io docker-compose-v2
```
**NVIDA GPU Support:** You will also need to install NVIDIA Container Toolkit, see instructions [here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). Make sure to reboot after installing!

#### Windows
Install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/)

**NVIDIA GPU Support:** This requires WSL. Follow the instructions [here](https://learn.microsoft.com/en-us/windows/wsl/install) to install it, then follow the rest of the [WSL/Linux](#wsllinux) instructions to get set up with Docker and continue using Vapor in your WSL CLI.

#### MacOS
Install [Docker Desktop for MacOS](https://docs.docker.com/desktop/setup/install/mac-install/)

**NOTE:** It is currently not possible to passthrough an Apple GPU to Ollama's docker container. 

### Start Services
Make sure you have set the `RESOURCE_PROFILE` variable in your `.env` according to what your device has available, then startup the backend services (including Ollama, Neo4j, FastMCP):
```shell
bash scripts/start.sh
```
Remember to shut down (if necessary) with:
```shell
bash scripts/stop.sh
```

## Usage
### Neo4j Database Population
First, you will need to populate the graph with data from Steam. This process will set you as the central node and populate in hops outwards from your friends (friends of friends, ..., etc.). See the usage here:
```shell
python vapor/populate.py -h
```
To populate/setup for the first time, enable all populating commands like so:
```shell
python vapor/populate.py -i -f -g -G -d --embed game-descriptions
```
**NOTE:** There are currently some issues with rate limiting when populating data from Steam. This will be fixed in the future, but for now it is advisable to keep a small dataset using the `limit` argument, e.g. `python vapor/populate.py <args> -l 50` will limit the total amount of friends per user to 50, and the number of games per user to 50. This is usually sufficient to avoid errors with rate limiting. Alternatively, you can populate datatypes one a time, and take a break in between. This is still prone to rate limiting but will grab as much data as possible.

Afterwards, you can run queries in the [Neo4j Browser](http://localhost:7474) and view the results. For example, to view the graph of Users and their "friendships":
```cypher
MATCH p=()-[:HAS_FRIEND]->() RETURN p LIMIT 50
```

### Chat
To start a chat with your configured LLM (see the `.env` file you created during [setup](#setup-environment)):
```shell
python vapor/chat.py
```
Then you can ask questions about the Steam data. Currently, this has very basic tooling support centered around information about the games in the database, for example:
```bash
Ask a question:
>>> What are some world war 2 games?
Here are some World War 2 games available:

 1 Company of Heroes - Legacy Edition - A real-time strategy game that begins with the D-Day Invasion of Normandy and
   follows Allied soldiers through pivotal WWII battles. Features cinematic single-player campaign, advanced squad AI,
   and stunning visuals.
 2 Darkest Hour: Europe '44-'45 - A first-person shooter with a terrifying suppression system, over 100 iconic weapons,
   and 90+ armored vehicles including late-war heavy tanks like the M18 Hellcat and King Tiger.
 3 Day of Defeat - An intense team-based FPS set in the WWII European Theatre of Operations. Players choose from
   infantry classes with historical weaponry and complete mission-specific objectives based on key historical
   operations.
 4 Mare Nostrum - Set in North Africa, this game features British, Australian, German, and Italian forces with authentic
   weaponry and 10 fully realized vehicles across 8 different battle environments.
 5 Red Orchestra: Ostfront 41-45 - The only FPS focused on the WWII Russian Front, featuring realistic bullet
   ballistics, 16 fully realized vehicles, 30 authentic infantry weapons, and support for 50+ player online multiplayer.

These games cover various aspects of WWII combat including strategy, first-person shooting, and different theaters of
war from Europe to North Africa.
```

## Development
Refer to this section only if you are developing the codebase. 

### Development Checklist
- [ ] Ensure [environment](#installation) is setup and activated
- [ ] Make code changes with proper [formatting](#code-formatting)
- [ ] Locally, ensure passing [unit tests](#unit-tests)
- [ ] Bump the [version](setup.py) with standard semantic versioning rules
- [ ] Create a [PR](#https://github.com/bbrillhart19/vapor/pulls) as a draft
- [ ] Trigger [CI/CD tests workflow](.github/workflows/test.yml) by marking the PR "Ready for review"
- [ ] Merge the PR after review and required approvals
- [ ] Create a [release](https://github.com/bbrillhart19/vapor/releases/) matching the updated version number

### Installation
#### Vapor Development Package
Install the editable `dev` flavor of the `vapor` package, preferably within a virtual environment, with:
```shell
pip install -e .[dev,all]
```

### Code Formatting
This codebase is formatted using `black`. Prior to pushing any changes/commits, format them with:
```shell
black vapor tests
```

### Unit Tests
A convenience script has been set up to launch the necessary [development containers](compose.dev.yaml) and subsequently run the tests and report coverage before spinning down the containers:
```shell
bash scripts/run-tests.sh
```
