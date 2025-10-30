import argparse
from time import sleep

from loguru import logger
from neo4j.exceptions import ServiceUnavailable

from vapor.clients import Neo4jClient
import globals


def wait_for_connection(timeout: int = 60, sleep_duration: int = 5):
    logger.info("Verifying Neo4j Connection >>>")
    time_remaining = timeout
    connected = False
    while not connected and time_remaining > 0:
        try:
            Neo4jClient(
                uri=globals.NEO4J_URI,
                auth=(globals.NEO4J_USER, globals.NEO4J_PW),
                database=globals.NEO4J_DATABASE,
            )
            connected = True
        except ServiceUnavailable:
            logger.warning(
                f"Connection attempt failed, time remaining={time_remaining}s"
            )
            sleep(sleep_duration)
            time_remaining -= sleep_duration

    if not connected:
        logger.error("Timeout reached, Neo4j connection failed!")
        raise ServiceUnavailable
    logger.success("Successfully connected to Neo4j >>>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Waits for verified connection to Neo4j dev instance."
    )
    parser.add_argument(
        "-t",
        "--timeout",
        help="Timeout, in seconds, to wait until raising a ServiceUnavailable error.",
        default=60,
    )
    parser.add_argument(
        "-d",
        "--sleep-duration",
        help="How long, in seconds, to wait to retry the connection after a failed attempt",
        default=5,
    )
    args = parser.parse_args()
    wait_for_connection(**args.__dict__)
