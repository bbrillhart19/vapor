from neo4j import Driver, GraphDatabase

from vapor.core.utils import utils

# Module-level driver instance (set by factory lifespan)
_driver: Driver | None = None


def create_driver() -> Driver:
    """Create a Neo4j driver instance from environment configuration.

    Returns:
        Driver: Configured Neo4j driver instance.
    """
    if utils.in_docker():
        neo4j_hostname = utils.get_env_var("NEO4J_DOCKER_HOST_NAME", "vapor-neo4j")
    else:
        neo4j_hostname = "localhost"
    neo4j_port = utils.get_env_var("NEO4J_BOLT_PORT", "7687")
    neo4j_uri = f"neo4j://{neo4j_hostname}:{neo4j_port}"
    return GraphDatabase.driver(
        uri=neo4j_uri,
        auth=(
            utils.get_env_var("NEO4J_USER"),
            utils.get_env_var("NEO4J_PW"),
        ),
        database=utils.get_env_var("NEO4J_DATABASE"),
    )


def get_driver() -> Driver:
    """Get the Neo4j driver instance.

    Returns:
        Driver: The Neo4j driver instance.

    Raises:
        RuntimeError: If driver has not been initialized.
    """
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialized")
    return _driver
