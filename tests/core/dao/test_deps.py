import pytest
from neo4j import Driver

from vapor.core.dao import driver, deps, GamesDAO


@pytest.mark.neo4j
def test_get_games_dao(neo4j_driver: Driver):
    """Tests get_games_dao returns a GamesDAO instance."""
    # Save original value
    original_driver = driver._driver
    try:
        driver._driver = neo4j_driver
        dao = deps.get_games_dao()
        assert isinstance(dao, GamesDAO)
        assert dao.driver is neo4j_driver
    finally:
        # Restore original
        driver._driver = original_driver
