from loguru import logger
from fastapi import FastAPI

from vapor.app import routes


@logger.catch
def create_app() -> FastAPI:
    """Creates the Vapor REST API application"""
    ### Create API ###
    logger.info("Creating Vapor API...")
    app = FastAPI(title="Vapor API")

    ### Add API Routers ###
    app.include_router(routes.status_router)

    return app
