import os
from pathlib import Path
import shutil


def get_env_var(env_key: str, non_env_val: str | None = None) -> str:
    if not non_env_val:
        return os.environ[env_key]
    return non_env_val


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
