from loguru import logger
from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from langchain.agents import create_agent

from vapor.utils import utils
from vapor.clients import Neo4jClient
from vapor.tools import GAME_TOOLS
from vapor import VaporContext

OLLAMA_LLM = utils.get_env_var("OLLAMA_LLM")


@logger.catch
def chat() -> None:
    # Setup neo4j client in dev mode
    logger.info("Setting development environment")
    utils.set_dev_env()
    logger.info("Initializing Neo4jClient...")
    neo4j_client = Neo4jClient.from_env()

    logger.info(f"Starting test with model={OLLAMA_LLM} >>>")
    context = VaporContext(neo4j_client=neo4j_client)

    model = ChatOllama(
        model=OLLAMA_LLM,
        validate_model_on_init=True,
        temperature=0.7,
    )

    prompt = """
        You are a helpful AI companion for gamers. Your tools will 
        help you access a graph database that has been pre-populated
        with data from Steam. Use these tools to help answer the questions
        from the user, who presumably would like to get information
        about video games. If you do not have a tool that pertains to the user's
        request, simply inform them that you cannot support that request, and
        provide additional information about requests that your tools can
        support. When receiving results from your tools, summarize them for
        the user so they are succinct but contain important information.        
    """

    agent = create_agent(
        model=model,
        tools=GAME_TOOLS,
        context_schema=VaporContext,
        system_prompt=prompt,
    )

    human_msg = HumanMessage("Tell me about helldivers 2")

    for event in agent.stream(
        {"messages": [human_msg]},
        context=context,
        stream_mode="values",
    ):
        event["messages"][-1].pretty_print()


if __name__ == "__main__":
    chat()
