from loguru import logger
from langchain.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph

from vapor.clients import Neo4jClient
from vapor.tools import GAME_TOOLS
from vapor.models.llm import VaporLLM
from vapor.models.prompts import load_prompt
from vapor import VaporContext


@logger.catch
def chat() -> None:
    """Opens a chat loop with Vapor's AI model serviced by Ollama"""
    logger.info("Initializing Neo4jClient...")
    neo4j_client = Neo4jClient.from_env()

    logger.info("Setting up context...")
    context = VaporContext(neo4j_client=neo4j_client)

    logger.info("Loading prompt...")
    prompt = load_prompt("chat")

    logger.info(f"Initializing LLM Agent...")
    llm = VaporLLM.from_env(temperature=0.7, num_ctx=4096)
    agent: CompiledStateGraph = create_agent(
        model=llm,
        tools=GAME_TOOLS,
        context_schema=VaporContext,
        system_prompt=prompt,
    )

    logger.success(f"Successfully initialized {llm.model} >>>")

    while True:
        try:
            msg = input("\nAsk a question:\n>>> ")
            human_msg = HumanMessage(msg)

            for event in agent.stream(
                {"messages": [human_msg]},
                context=context,
                stream_mode="values",
            ):
                event["messages"][-1].pretty_print()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    chat()
