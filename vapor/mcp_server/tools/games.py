from fastmcp import FastMCP
from fastmcp.dependencies import Depends

from vapor.core.dao import GamesDAO
from vapor.core.dao.deps import get_games_dao
from vapor.core.models.embeddings import VaporEmbeddings, get_embedder


class GamesTools(object):
    def __init__(
        self,
        mcp_instance: FastMCP,
    ):
        mcp_instance.tool(self.about_the_game)
        mcp_instance.tool(self.find_similar_games)

    async def about_the_game(
        self, name: str, dao: GamesDAO = Depends(get_games_dao)
    ) -> dict[str, str]:
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
            dict[str, str]: Dictionary with fields describing the game
                with the title that best matched the query name. The "matched_game"
                field will provide the name/title of the game that best matched the
                query name, or will not be present if no match was found.
                The "about_the_game" field will provide the game description
                for the best matched game, or will not be present
                if no pre-populated description is available.
        """
        return dao.about_the_game(name)

    async def find_similar_games(
        self,
        summarized_description: str,
        dao: GamesDAO = Depends(get_games_dao),
        embedder: VaporEmbeddings = Depends(get_embedder),
    ) -> list[dict]:
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
            list[dict]: List of dictionaries for each discovered similar
                game as well as the description chunks most similar
                to the `summarized_description`. Each discovered similar game
                will include a "name" field with the title of the game,
                a "appid" field with the unique Steam game ID of the game,
                and a "description_chunks" field which will contain a list
                of each similar description excerpt from the game.
                If no similar games are found, the returned response
                will be an empty list.
        """
        # Create an embedding of the summarized description
        embedding = embedder.embed_query(summarized_description)
        # Use DAO to perform semantic search
        return dao.find_similar_games(
            embedding=embedding,
            n_neighbors=10,
            min_score=0.5,
        )
