import pandas as pd
from neo4j import Transaction


class GamesDAO(object):

    @staticmethod
    def search_by_name(tx: Transaction, name: str) -> pd.DataFrame:
        """Searches all `Game` nodes for those that closely match
        the provided `name` which may not be exact. The method requires
        the APOC Neo4j plugin to use `apoc.text.fuzzyMatch` and
        `apoc.text.clean` to find the best match.

        Args:
            name (str): The name of the game to search for.

        Returns:
            pd.DataFrame: The table of matched games, with "appid"
                and "name" values. If no game is found, this table will
                be empty. If multiple matches are found,
                they will be sorted in ascending order of their
                Levenshtein distances, best match will be the first row.
        """
        cypher = """
            WITH apoc.text.clean($name) as clean_name
            MATCH (g:Game)
            WHERE apoc.text.fuzzyMatch(apoc.text.clean(g.name), clean_name) = TRUE
            RETURN
                g.appId as appid,
                g.name as name,
                apoc.text.distance(apoc.text.clean(g.name), clean_name) as distance
        """
        result = tx.run(cypher, name=name)
        return result.to_df().sort_values(by="distance", ignore_index=True)

    @staticmethod
    def get_description_by_appid(tx: Transaction, appid: int) -> pd.DataFrame:
        """Retrieves the "about the game" description for a specific game
        by its Steam app ID.

        Args:
            appid (int): The Steam app ID of the game.

        Returns:
            pd.DataFrame: A single-row dataframe with the "about_the_game"
                column if the game exists and has a description, otherwise
                an empty dataframe.
        """
        cypher = """
            MATCH (g:Game {appId: $appid})
            RETURN g.aboutTheGame as about_the_game
        """
        result = tx.run(cypher, appid=appid)
        return result.to_df()

    @staticmethod
    def semantic_search_descriptions(
        tx: Transaction,
        embedding: list[float],
        n_neighbors: int,
        min_score: float,
    ) -> pd.DataFrame:
        """Performs semantic similarity search over game description embeddings
        using vector index search.

        Args:
            embedding (list[float]): The query embedding vector.
            n_neighbors (int): Maximum number of similar items to return.
            min_score (float): Minimum similarity score threshold (0.0 to 1.0).

        Returns:
            pd.DataFrame: Table with columns: name, appid, desc (description chunk),
                and score. Sorted by similarity score (highest first).
        """
        cypher = """
            CALL db.index.vector.queryNodes(
                "game_description_index",
                $n_neighbors,
                $embedding
            ) YIELD node, score
            WHERE score >= $min_score
            MATCH (g:Game {appId: node.source})
            RETURN
                g.name as name,
                g.appId as appid,
                substring(g.aboutTheGame, node.startIndex, node.totalLength) as desc,
                score
        """
        result = tx.run(
            cypher,
            embedding=embedding,
            n_neighbors=n_neighbors,
            min_score=min_score,
        )
        return result.to_df()
