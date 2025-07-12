from typing import Any
import pytest

from vapor.utils import utils
from vapor.clients import Neo4jClient, SteamClient

# TODO: Create a "test" environment that creates an empty database
# and yields it before using DETACH DELETE to empty it

@pytest.fixture(scope="session", autouse=True)
def env() -> None:
    utils.load_env()

@pytest.fixture(scope="session")
def neo4j_client() -> Neo4jClient:
    return Neo4jClient.from_env()

