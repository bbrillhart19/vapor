import pandas as pd
from neo4j import Transaction

from vapor.app.db.uow import Neo4jUnitOfWork
from vapor.app.dao import GamesDAO


class GamesService(object):
    def __init__(self, uow: Neo4jUnitOfWork):
        self.uow = uow

    def best_match_by_name(self, name: str) -> dict | None:
        result = self.uow.read(lambda tx: GamesDAO.search_by_name(tx, name=name))
        if result.empty:
            return None
        return result.iloc[0].to_dict()
