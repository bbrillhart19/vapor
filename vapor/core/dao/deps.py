from .driver import get_driver
from . import GamesDAO


def get_games_dao() -> GamesDAO:
    """Get the games DAO instance.

    Returns:
        GamesDAO: A games DAO instance.
    """
    return GamesDAO(get_driver())
