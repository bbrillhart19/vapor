"""Miscellaneous utility methods"""

from typing import Any
import os


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


def set_dev_env() -> None:
    """Overrides specific environment variables to use values
    hardcoded for dev instances of external services/resources.
    """
    set_env({"NEO4J_URI": "neo4j://localhost:7688", "NEO4J_PW": "neo4j-dev"})
