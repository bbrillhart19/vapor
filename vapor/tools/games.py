import json
from langchain.tools import tool, ToolRuntime

from vapor import VaporContext


@tool
def about_the_game(name: str, runtime: ToolRuntime[VaporContext]) -> str:
    """Retrieves the "about the game" description for the game
    in the database that best matches the provided `name` using
    a fuzzy match technique. The game descriptions have been populated
    in the database from Steam.

    Args:
        name (str): The name of the game to search for and
            retrieve the game description for. This is not
            expected to be a perfect character-for-character
            match to the stored game titles.

    Returns:
        str: The JSON-formatted text describing the game with the title that
            best matched the query name. The "matched_game" field will
            provide the name/title of the game that best matched the
            query name, or will not be present if no match was found.
            The "about_the_game" field will provide the game description
            for the best matched game, or will not be present
            if no pre-populated description is available.
    """
    # Set up response
    response: dict[str, str] = {}
    # Get the matches from neo4j
    matches = runtime.context.neo4j_client.search_game_by_name(name)
    # Return empty response if nothing matched the query
    if matches.empty:
        return json.dumps(response)

    # Matches were found, take the best (first row)
    best_match = matches.iloc[0]
    response["matched_game"] = best_match["name"]

    # Get the about the game description
    cypher = """
        MATCH (g:Game {appId: $appid})
        RETURN g.aboutTheGame as about_the_game
    """
    description = runtime.context.neo4j_client._read(
        cypher, appid=best_match["appid"]
    ).iloc[0]["about_the_game"]
    # Return response with no description if not available
    if not description:
        return json.dumps(response)

    # Add retrieved description and return
    response["about_the_game"] = description
    return json.dumps(response)
