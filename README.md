Vapor
-------

A (to-be) GraphRAG based video game recommendation system with Steam Web API and Neo4j.

## Getting Started
Before proceeding, clone the repository to your system.

### Requirements
- Python
- Pip
- [Docker](#docker-installation)

### Installation
Install the editable `vapor` package, preferably within a virtual environment, with:
```shell
pip install .
```

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

### Start Neo4j
[Neo4j](https://neo4j.com/) is a GraphDB which is used by `vapor` to store your interactions with different games and users. Before doing anything else, spin up the `neo4j` server with:
```shell
docker compose up -d
```
If all went well, you should be able to navigate to http://localhost:7474 in your browser and view the `noe4j` database. If you know the [Cypher query language](https://neo4j.com/docs/cypher-manual/current/introduction/) this is where you can write queries to view parts of your "Vapor Graph" once it is [populated](#graph-population).

## Usage

### Steam to Neo4j
First, you will need to populate the graph with data from Steam. This process will set you as the central node and populate in hops outwards from your friends (friends of friends, ..., etc.). See the usage here:
```shell
python vapor/steam2neo4j.py -h
```
To populate/setup for the first time, enable all populating commands like so:
```shell
python vapor/steam2neo4j.py -i -f -g -G
```
Afterwards, you can run queries in the [Neo4j Browser](http://localhost:7474) and view the results. For example, to view the graph of Users and their "friendships":
```cypher
MATCH p=()-[:HAS_FRIEND]->() RETURN p LIMIT 50
```

## Development
Refer to this section only if you are developing the codebase. 

### Installation
Install the editable `dev` flavor of the `vapor` package, preferably within a virtual environment, with:
```shell
pip install -e .[dev]
```

### Development Checklist
- [ ] Ensure [environment](#installation) is setup and activated
- [ ] Make code changes with proper [formatting](#code-formatting)
- [ ] TODO: Locally, ensure passing [unit tests](#unit-tests)
- [ ] TODO: Additionally run necessary [integration tests](#integration-tests)
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
