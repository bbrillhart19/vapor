import os


def get_env_var(env_key: str, non_env_val: str | None = None) -> str:
    if not non_env_val:
        return os.environ[env_key]
    return non_env_val
