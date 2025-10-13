from dotenv import load_dotenv

from .utils import utils, logging

# Set up environment file and load
ENV_FILE = utils.cast_path(utils.get_env_var("VAPOR_ENV", "./.env"))
if not ENV_FILE.exists():
    raise FileNotFoundError(f"Could not load environment from file={ENV_FILE}")
load_dotenv(ENV_FILE)

# Set up path for data
DATA_PATH = utils.cast_path(utils.get_env_var("VAPOR_DATA_PATH"))

# Initialize the log file/logger instance
logging.init_logger()
