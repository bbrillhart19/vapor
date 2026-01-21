from vapor.core.db.uow import Neo4jUnitOfWork
from vapor.core.dao import GamesDAO


class GamesService(object):
    def __init__(self, uow: Neo4jUnitOfWork):
        self.uow = uow

    def best_match_by_name(self, name: str) -> dict | None:
        """Find the best matching game by name using fuzzy matching.

        Args:
            name (str): The name of the game to search for.

        Returns:
            dict | None: Dictionary with "appid", "name", and "distance" fields
                if a match is found, otherwise None.
        """
        result = self.uow.read(lambda tx: GamesDAO.search_by_name(tx, name=name))
        if result.empty:
            return None
        return result.iloc[0].to_dict()

    def about_the_game(self, name: str) -> dict[str, str]:
        """Retrieves the "about the game" description for the game
        that best matches the provided name using fuzzy matching.

        Args:
            name (str): The name of the game to search for.

        Returns:
            dict[str, str]: Dictionary with "matched_game" and "about_the_game"
                fields if a match with description is found. If no match is found,
                returns empty dict. If match found but no description, returns
                only "matched_game" field.
        """
        response: dict[str, str] = {}

        # Find best matching game by name
        best_match = self.best_match_by_name(name)
        if not best_match:
            return response

        response["matched_game"] = best_match["name"]

        # Get the game description
        result = self.uow.read(
            lambda tx: GamesDAO.get_description_by_appid(tx, appid=best_match["appid"])
        )

        if result.empty:
            return response

        description = result.iloc[0]["about_the_game"]
        if not description:
            return response

        response["about_the_game"] = description
        return response

    def find_similar_games(
        self,
        embedding: list[float],
        n_neighbors: int = 10,
        min_score: float = 0.5,
    ) -> list[dict]:
        """Finds games with descriptions semantically similar to the provided
        embedding vector.

        Args:
            embedding (list[float]): The query embedding vector.
            n_neighbors (int, optional): Maximum number of similar games to return.
                Defaults to 10.
            min_score (float, optional): Minimum similarity score threshold.
                Defaults to 0.5.

        Returns:
            list[dict]: List of dictionaries, each containing:
                - "name": Game title
                - "appid": Steam app ID
                - "description_chunks": List of similar description excerpts
                Returns empty list if no similar games found.
        """
        result = self.uow.read(
            lambda tx: GamesDAO.semantic_search_descriptions(
                tx,
                embedding=embedding,
                n_neighbors=n_neighbors,
                min_score=min_score,
            )
        )

        if result.empty:
            return []

        # Group results by game and aggregate description chunks
        parsed_results = []
        for name, game_df in result.groupby(by="name"):
            appid = game_df.iloc[0]["appid"]
            parsed_result = {
                "name": name,
                "appid": int(appid),
                "description_chunks": game_df["desc"].values.tolist(),
            }
            parsed_results.append(parsed_result)

        return parsed_results
