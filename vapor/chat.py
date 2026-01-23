"""CLI chat client that communicates with the Vapor REST API."""

import asyncio
import json

import httpx
from loguru import logger
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.json import JSON

from vapor.core.utils import utils


async def handle_chat(client: httpx.AsyncClient, api_url: str) -> None:
    """Handle a single chat interaction via the API.

    Args:
        client: The HTTP client for API requests.
        api_url: Base URL of the chat API.
    """
    console = Console()
    msg = console.input("\nAsk a question:\n>>> ")
    content_buffer = ""
    event_type = None
    live: Live | None = None

    async with client.stream(
        "POST",
        f"{api_url}/chat",
        json={"message": msg},
        timeout=120.0,
    ) as response:
        async for line in response.aiter_lines():
            if not line:
                continue

            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())

                if event_type == "tool_call":
                    # Stop live display if active to show panel
                    if live is not None:
                        live.stop()
                        live = None
                    console.print(
                        Panel(
                            f"Tool Name: {data['tool_name']}",
                            title=f"[yellow]Tool Call[/yellow]",
                        )
                    )
                elif event_type == "tool_result":
                    console.print(
                        Panel(
                            f"Tool Name: {data['tool_name']}",
                            title=f"[green]Tool Result[/green]",
                        )
                    )
                elif event_type == "content":
                    content_buffer += data["text"]
                    # Start live display on first content chunk
                    if live is None:
                        live = Live(
                            Markdown(content_buffer),
                            console=console,
                            refresh_per_second=15,
                        )
                        live.start()
                    else:
                        live.update(Markdown(content_buffer))
                elif event_type == "done":
                    break

    # Stop live display when done
    if live is not None:
        live.stop()


@logger.catch(reraise=True)
async def chat() -> None:
    """Opens a chat loop communicating with Vapor API."""
    logger.info("Connecting to Vapor API...")

    app_port = utils.get_env_var("APP_PORT", "8000")
    api_url = f"http://localhost:{app_port}"

    async with httpx.AsyncClient() as client:
        # Verify API is healthy
        health = await client.get(f"{api_url}/status/health")
        if health.status_code != 200:
            raise RuntimeError("Vapor API is not healthy")

        logger.success("Connected to Vapor API")

        while True:
            try:
                await handle_chat(client, api_url)
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break


if __name__ == "__main__":
    asyncio.run(chat())
