from loguru import logger

from vapor.utils import utils


def init_logger(name: str = "vapor", **kwargs) -> None:
    """Initialize the Vapor logger"""
    # Create logs directory and filename
    log_folder = utils.create_dir(utils.get_env_var("VAPOR_LOGS_PATH"))
    logfile = log_folder.joinpath(name + "_{time}.log")

    # Add to logger w/ extra kwargs
    logger.add(logfile, **kwargs)
    logger.info(f"Initialized logger")
