import asyncio

from loguru import logger
from rich.console import Console
from rich.markdown import Markdown

from langchain.messages import HumanMessage, AIMessage
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph
from langchain_mcp_adapters.client import MultiServerMCPClient

from vapor.core.models.llm import VaporLLM
from vapor.core.models.prompts import load_prompt


async def handle_chat(agent: CompiledStateGraph) -> None:
    """Helper method to handle user chat questions"""
    console = Console()
    msg = console.input("\nAsk a question:\n>>> ")
    human_msg = HumanMessage(msg)

    async for event in agent.astream(
        {"messages": [human_msg]},
        stream_mode="values",
    ):
        message = event["messages"][-1]
        if isinstance(message, AIMessage):
            md = Markdown(message.content)
            console.print(md)


@logger.catch(reraise=True)
async def chat() -> None:
    """Opens a chat loop with Vapor's AI model serviced by Ollama"""
    logger.info("Loading prompt...")
    prompt = load_prompt("chat")

    logger.info(f"Initializing LLM Agent...")
    llm = VaporLLM.from_env(temperature=0.7, num_ctx=4096)

    logger.info("Connecting to MCP Server...")
    client = MultiServerMCPClient(
        {
            "vapor-mcp": {
                "transport": "http",
                "url": "http://localhost:8000/mcp",
            }
        }
    )

    tools = await client.get_tools()

    agent: CompiledStateGraph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt,
    )

    logger.success(f"Successfully initialized {llm.model} >>>")

    while True:
        try:
            await handle_chat(agent)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    asyncio.run(chat())
