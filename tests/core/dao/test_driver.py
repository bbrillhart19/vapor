import os

import pytest
from neo4j import Driver

from vapor.core.dao import driver
from vapor.core.utils import utils

from helpers import globals


@pytest.mark.parametrize("in_docker", [True, False])
@pytest.mark.neo4j
def test_create_driver(mocker, in_docker: bool):
    """Tests create_driver with different environments."""
    mocker.patch.object(utils, "in_docker", return_value=in_docker)
    mocker.patch.dict(
        os.environ,
        {
            "NEO4J_DOCKER_HOST_NAME": globals.NEO4J_DOCKER_HOST_NAME,
            "NEO4J_BOLT_PORT": globals.NEO4J_BOLT_PORT,
            "NEO4J_USER": globals.NEO4J_USER,
            "NEO4J_PW": globals.NEO4J_PW,
            "NEO4J_DATABASE": globals.NEO4J_DATABASE,
        },
    )
    created_driver = driver.create_driver()
    assert isinstance(created_driver, Driver)
    created_driver.close()


def test_get_driver_not_initialized():
    """Tests get_driver raises error when driver not initialized."""
    # Save original value
    original_driver = driver._driver
    try:
        driver._driver = None
        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            driver.get_driver()
    finally:
        # Restore original
        driver._driver = original_driver


@pytest.mark.neo4j
def test_get_driver_initialized(neo4j_driver: Driver):
    """Tests get_driver returns driver when initialized."""
    # Save original value
    original_driver = driver._driver
    try:
        driver._driver = neo4j_driver
        result = driver.get_driver()
        assert result is neo4j_driver
    finally:
        # Restore original
        driver._driver = original_driver
