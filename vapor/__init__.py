from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

from .core.utils import utils

# Set up environment file and load
ENV_FILE = utils.get_env_var("VAPOR_ENV", "./.env")
if Path(ENV_FILE).exists():
    load_dotenv(ENV_FILE)
    logger.info(f"Loaded environment from: {ENV_FILE}")
else:
    logger.warning(f"Environment file not found @ {ENV_FILE}")  # pragma: nocover
