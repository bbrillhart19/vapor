from dotenv import load_dotenv

from vapor._types import *
from .utils import utils

# Set up environment file and load
ENV_FILE = utils.get_env_var("VAPOR_ENV", "./.env")
load_dotenv(ENV_FILE)
