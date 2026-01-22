from fastmcp import FastMCP
from fastmcp.dependencies import Depends

from vapor.core.dao import GamesDAO
from vapor.core.dao.deps import get_games_dao
from vapor.core.models.embeddings import VaporEmbeddings, get_embedder
from vapor.mcp_server.schemas import (
    AboutTheGameResponse,
    FindSimilarGamesResponse,
    SimilarGame,
)


class GamesTools(object):
    def __init__(
        self,
        mcp_instance: FastMCP,
    ):
        mcp_instance.tool(self.about_the_game)
        mcp_instance.tool(self.find_similar_games)

    async def about_the_game(
        self, name: str, dao: GamesDAO = Depends(get_games_dao)
    ) -> AboutTheGameResponse:
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
            AboutTheGameResponse: Response containing the matched game name
                and its description. Fields will be None if no match was found
                or if the matched game has no description available.
        """
        result = dao.about_the_game(name)
        return AboutTheGameResponse(
            matched_game=result.get("matched_game"),
            about_the_game=result.get("about_the_game"),
        )

    async def find_similar_games(
        self,
        summarized_description: str,
        dao: GamesDAO = Depends(get_games_dao),
        embedder: VaporEmbeddings = Depends(get_embedder),
    ) -> FindSimilarGamesResponse:
        """Finds games and excerpts of their "about the game" descriptions
        in the database which are semantically similar to the
        provided `summarized_description`. Provides the discovered games
        and their respective excerpts of similar descriptions.

        Args:
            summarized_description (str): A summarized game description
                that may be tailored to highlight specific information
                about the game to discover games which are similar
                in specific ways. This will be embedded and used as such
                for semantic similarity search in the vector database.

        Returns:
            FindSimilarGamesResponse: Response containing a list of similar games,
                each with the game name, Steam app ID, and description chunks
                that were semantically similar to the query. The list will be
                empty if no similar games were found.
        """
        # Create an embedding of the summarized description
        embedding = embedder.embed_query(summarized_description)
        # Use DAO to perform semantic search
        results = dao.find_similar_games(
            embedding=embedding,
            n_neighbors=10,
            min_score=0.5,
        )
        return FindSimilarGamesResponse(
            similar_games=[SimilarGame(**game) for game in results]
        )
