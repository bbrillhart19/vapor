from pathlib import Path


PROMPTS_DIR = Path("./.agents")


def load_prompt(name: str) -> str:
    prompt_file = PROMPTS_DIR.joinpath(f"{name}.md")
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found @ {prompt_file}")
    with open(prompt_file, "r") as f:
        content = f.read()
    return content
