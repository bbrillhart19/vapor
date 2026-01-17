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
