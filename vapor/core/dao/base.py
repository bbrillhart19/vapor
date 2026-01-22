from neo4j import Driver


class BaseDAO:
    """Base Data Access Object that provides database read/write operations."""

    def __init__(self, driver: Driver):
        self.driver = driver

    def read(self, fn):
        """Execute a read transaction.

        Args:
            fn: A callable that takes a transaction and returns a result.

        Returns:
            The result from the transaction function.
        """
        with self.driver.session() as session:
            return session.execute_read(fn)

    def write(self, fn):
        """Execute a write transaction.

        Args:
            fn: A callable that takes a transaction and returns a result.

        Returns:
            The result from the transaction function.
        """
        with self.driver.session() as session:
            return session.execute_write(fn)
