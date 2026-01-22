from pydantic import BaseModel, Field


class AboutTheGameResponse(BaseModel):
    """Response model for the about_the_game tool.

    Contains the matched game name and its description from Steam.
    Fields are optional since a match may not be found or the
    matched game may not have a description available.
    """

    matched_game: str | None = Field(
        default=None,
        description="The name/title of the game that best matched the query name "
        "using fuzzy matching. None if no match was found.",
    )
    about_the_game: str | None = Field(
        default=None,
        description="The 'about the game' description from Steam for the matched game. "
        "None if no description is available or no match was found.",
    )


class SimilarGame(BaseModel):
    """A single game found through semantic similarity search."""

    name: str = Field(description="The title of the game.")
    appid: int = Field(description="The unique Steam application ID for the game.")
    description_chunks: list[str] = Field(
        description="List of description excerpts from this game that were "
        "semantically similar to the search query."
    )


class FindSimilarGamesResponse(BaseModel):
    """Response model for the find_similar_games tool.

    Contains a list of games with descriptions semantically similar
    to the provided summarized description.
    """

    similar_games: list[SimilarGame] = Field(
        default_factory=list,
        description="List of games with semantically similar descriptions. "
        "Empty if no similar games were found.",
    )
