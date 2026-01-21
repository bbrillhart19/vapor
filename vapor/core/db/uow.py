from neo4j import Driver


class Neo4jUnitOfWork:
    def __init__(self, driver: Driver):
        self.driver = driver

    def read(self, fn):
        with self.driver.session() as session:
            return session.execute_read(fn)

    def write(self, fn):
        with self.driver.session() as session:
            return session.execute_write(fn)
