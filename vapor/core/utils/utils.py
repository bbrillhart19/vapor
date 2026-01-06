"""Miscellaneous utility methods"""

from typing import Any
import os
from pathlib import Path


def get_env_var(env_key: str, default: str | None = None) -> str:
    """Retrieves the environment variable value from `os.environ`
    with similar behavior as `os.getenv(env_key, default)` except
    if `default` is None and the `env_key` is not found or is empty,
    an error is raised.
    """
    if env_key in os.environ:
        env_val = os.environ[env_key]
        if env_val == "" or env_val is None:
            if not default:
                raise ValueError(
                    f"{env_key} found in env but is empty and no default provided."
                )
            return default
        return env_val

    if default is None:
        raise KeyError(f"{env_key} not found in env and no default provided.")
    return default


def set_env(env_mapping: dict[str, Any]) -> None:
    """Overrides specific environment variables to use values
    as supplied by `env_mapping`.
    """
    for k, v in env_mapping.items():
        os.environ[k] = v


def in_docker() -> bool:
    """Checks for `/.dockerenv` file to determine if we are in a docker process.
    This is mildly hacky but useful in case, for example, env vars need adjustment.
    """
    return Path("/.dockerenv").exists()
