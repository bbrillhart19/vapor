from vapor.app.db.uow import Neo4jUnitOfWork
from vapor.app.db.driver import get_driver
from vapor.app.services import GamesService


def get_uow():
    return Neo4jUnitOfWork(get_driver())


def get_games_service() -> GamesService:
    return GamesService(get_uow())
