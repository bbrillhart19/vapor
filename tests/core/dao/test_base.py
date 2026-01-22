import pytest
from neo4j import Driver

from vapor.core.dao import BaseDAO


@pytest.mark.neo4j
def test_base_dao_init(neo4j_driver: Driver):
    """Tests BaseDAO initialization with a driver."""
    dao = BaseDAO(neo4j_driver)
    assert dao.driver is neo4j_driver


@pytest.mark.neo4j
def test_base_dao_read(neo4j_driver: Driver):
    """Tests BaseDAO read transaction execution."""
    dao = BaseDAO(neo4j_driver)

    # First write some data
    def _write(tx):
        tx.run("MERGE (n:TestNode {name: 'test'})")

    dao.write(_write)

    # Now read it back
    def _read(tx):
        result = tx.run("MATCH (n:TestNode {name: 'test'}) RETURN n.name as name")
        return result.to_df()

    result = dao.read(_read)
    assert len(result) == 1
    assert result.iloc[0]["name"] == "test"


@pytest.mark.neo4j
def test_base_dao_write(neo4j_driver: Driver):
    """Tests BaseDAO write transaction execution."""
    dao = BaseDAO(neo4j_driver)

    # Write data
    def _write(tx):
        tx.run("MERGE (n:TestNode {name: $name})", name="write_test")

    dao.write(_write)

    # Verify it was written
    def _read(tx):
        result = tx.run("MATCH (n:TestNode {name: 'write_test'}) RETURN n.name as name")
        return result.to_df()

    result = dao.read(_read)
    assert len(result) == 1
    assert result.iloc[0]["name"] == "write_test"


@pytest.mark.neo4j
def test_base_dao_read_empty(neo4j_driver: Driver):
    """Tests BaseDAO read when no data exists."""
    dao = BaseDAO(neo4j_driver)

    def _read(tx):
        result = tx.run("MATCH (n:NonExistent) RETURN n")
        return result.to_df()

    result = dao.read(_read)
    assert result.empty
