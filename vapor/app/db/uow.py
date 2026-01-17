from typing import Protocol, Callable, TypeVar
from neo4j import Driver, Session

from vapor.app.db.driver import get_driver


class Neo4jUnitOfWork:
    def __init__(self, driver: Driver | None = None):
        self.driver = driver or get_driver()

    def read(self, fn):
        with self.driver.session() as session:
            return session.execute_read(fn)

    def write(self, fn):
        with self.driver.session() as session:
            return session.execute_write(fn)
