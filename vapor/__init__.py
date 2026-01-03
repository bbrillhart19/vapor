from dotenv import load_dotenv
from loguru import logger

from .core.utils import utils

# TODO: Do not load the environment file. It causes too many problems with docker.

# Set up environment file and load
ENV_FILE = utils.get_env_var("VAPOR_ENV", "./.env")
load_dotenv(ENV_FILE)
logger.info(f"Loaded environment from: {ENV_FILE}")
