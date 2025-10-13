import os
from pathlib import Path
import shutil
from dotenv import load_dotenv


def cast_path(pth: Path | str) -> Path:
    if isinstance(pth, str):
        return Path(pth)
    return pth


def create_dir(pth: Path | str, clear_contents: bool = False) -> Path:
    pth = cast_path(pth)
    if pth.exists() and clear_contents:
        shutil.rmtree(pth)
    pth.mkdir(exist_ok=True, parents=True)
    return pth


def load_env(env_file: Path | str | None = "./.env") -> None:
    if env_file:
        if cast_path(env_file).exists():
            load_dotenv(env_file, override=True)
            print(f"Loaded environment from file={env_file}")
        else:
            raise FileNotFoundError(f"Could not load environment from file={env_file}")
    else:
        print("No environment file provided, environment loaded from system.")


def get_env_var(env_key: str, non_env_val: str | None = None) -> str:
    if not non_env_val:
        return os.environ[env_key]
    return non_env_val
