from vapor.core.db.driver import get_driver
from vapor.core.db.uow import Neo4jUnitOfWork
from . import GamesService


def get_uow() -> Neo4jUnitOfWork:
    """Get a Unit of Work instance for Neo4j transactions.

    Returns:
        Neo4jUnitOfWork: A Unit of Work instance.
    """
    return Neo4jUnitOfWork(get_driver())


def get_games_service() -> GamesService:
    """Get the games service instance.

    Returns:
        GamesService: A games service instance.
    """
    return GamesService(get_uow())
