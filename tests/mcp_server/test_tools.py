import pytest
from fastmcp import FastMCP

from vapor.core.dao import GamesDAO
from vapor.core.models.embeddings import VaporEmbeddings
from vapor.mcp_server.tools.games import GamesTools
from vapor.mcp_server.schemas import (
    AboutTheGameResponse,
    FindSimilarGamesResponse,
    SimilarGame,
)


class TestGamesToolsInit:
    """Tests for GamesTools initialization."""

    def test_init_registers_tools(self, mock_mcp: FastMCP):
        """Tests that GamesTools registers its tools with the MCP instance."""
        tools = GamesTools(mcp_instance=mock_mcp)
        # Verify tool registration was called (mocked)
        assert mock_mcp.tool.call_count == 2


class TestAboutTheGameTool:
    """Tests for the about_the_game tool."""

    async def test_about_the_game_no_match(self, mocker, mock_mcp: FastMCP):
        """Tests about_the_game when no game matches."""
        # Mock the DAO
        mock_dao = mocker.MagicMock(spec=GamesDAO)
        mock_dao.about_the_game.return_value = {}

        tools = GamesTools(mcp_instance=mock_mcp)
        result = await tools.about_the_game(name="nonexistent game", dao=mock_dao)

        assert isinstance(result, AboutTheGameResponse)
        assert result.matched_game is None
        assert result.about_the_game is None
        mock_dao.about_the_game.assert_called_once_with("nonexistent game")

    async def test_about_the_game_match_no_description(self, mocker, mock_mcp: FastMCP):
        """Tests about_the_game when game matches but has no description."""
        mock_dao = mocker.MagicMock(spec=GamesDAO)
        mock_dao.about_the_game.return_value = {"matched_game": "Test Game"}

        tools = GamesTools(mcp_instance=mock_mcp)
        result = await tools.about_the_game(name="test game", dao=mock_dao)

        assert isinstance(result, AboutTheGameResponse)
        assert result.matched_game == "Test Game"
        assert result.about_the_game is None

    async def test_about_the_game_with_description(self, mocker, mock_mcp: FastMCP):
        """Tests about_the_game when game matches and has description."""
        mock_dao = mocker.MagicMock(spec=GamesDAO)
        mock_dao.about_the_game.return_value = {
            "matched_game": "Test Game",
            "about_the_game": "This is a test game description",
        }

        tools = GamesTools(mcp_instance=mock_mcp)
        result = await tools.about_the_game(name="test game", dao=mock_dao)

        assert isinstance(result, AboutTheGameResponse)
        assert result.matched_game == "Test Game"
        assert result.about_the_game == "This is a test game description"


class TestFindSimilarGamesTool:
    """Tests for the find_similar_games tool."""

    async def test_find_similar_games_no_results(
        self, mocker, mock_mcp: FastMCP, mock_embedder: VaporEmbeddings
    ):
        """Tests find_similar_games when no similar games found."""
        mock_dao = mocker.MagicMock(spec=GamesDAO)
        mock_dao.find_similar_games.return_value = []

        tools = GamesTools(mcp_instance=mock_mcp)
        result = await tools.find_similar_games(
            summarized_description="A fantasy RPG game",
            dao=mock_dao,
            embedder=mock_embedder,
        )

        assert isinstance(result, FindSimilarGamesResponse)
        assert result.similar_games == []
        mock_embedder.embed_query.assert_called_once_with("A fantasy RPG game")
        mock_dao.find_similar_games.assert_called_once()

    async def test_find_similar_games_with_results(
        self, mocker, mock_mcp: FastMCP, mock_embedder: VaporEmbeddings
    ):
        """Tests find_similar_games when similar games are found."""
        mock_dao = mocker.MagicMock(spec=GamesDAO)
        mock_dao.find_similar_games.return_value = [
            {
                "name": "Similar Game 1",
                "appid": 1000,
                "description_chunks": ["This is a fantasy RPG"],
            },
            {
                "name": "Similar Game 2",
                "appid": 1001,
                "description_chunks": ["Another fantasy adventure"],
            },
        ]

        tools = GamesTools(mcp_instance=mock_mcp)
        result = await tools.find_similar_games(
            summarized_description="A fantasy RPG game",
            dao=mock_dao,
            embedder=mock_embedder,
        )

        assert isinstance(result, FindSimilarGamesResponse)
        assert len(result.similar_games) == 2
        assert all(isinstance(g, SimilarGame) for g in result.similar_games)
        assert result.similar_games[0].name == "Similar Game 1"
        assert result.similar_games[0].appid == 1000
        assert result.similar_games[1].name == "Similar Game 2"
        assert result.similar_games[1].appid == 1001

    async def test_find_similar_games_multiple_chunks(
        self, mocker, mock_mcp: FastMCP, mock_embedder: VaporEmbeddings
    ):
        """Tests find_similar_games with multiple description chunks per game."""
        mock_dao = mocker.MagicMock(spec=GamesDAO)
        mock_dao.find_similar_games.return_value = [
            {
                "name": "Game With Multiple Chunks",
                "appid": 1000,
                "description_chunks": [
                    "This is the first chunk about the game.",
                    "This is the second chunk with more details.",
                    "And a third chunk with additional info.",
                ],
            },
        ]

        tools = GamesTools(mcp_instance=mock_mcp)
        result = await tools.find_similar_games(
            summarized_description="A detailed game",
            dao=mock_dao,
            embedder=mock_embedder,
        )

        assert len(result.similar_games) == 1
        assert len(result.similar_games[0].description_chunks) == 3

    async def test_find_similar_games_calls_dao_with_correct_params(
        self, mocker, mock_mcp: FastMCP, mock_embedder: VaporEmbeddings
    ):
        """Tests that find_similar_games passes correct parameters to DAO."""
        mock_dao = mocker.MagicMock(spec=GamesDAO)
        mock_dao.find_similar_games.return_value = []

        tools = GamesTools(mcp_instance=mock_mcp)
        await tools.find_similar_games(
            summarized_description="test",
            dao=mock_dao,
            embedder=mock_embedder,
        )

        # Verify the embedding was passed and correct parameters used
        call_kwargs = mock_dao.find_similar_games.call_args.kwargs
        assert "embedding" in call_kwargs
        assert call_kwargs["n_neighbors"] == 10
        assert call_kwargs["min_score"] == 0.5


class TestSchemasValidation:
    """Tests for Pydantic schema validation."""

    def test_about_the_game_response_defaults(self):
        """Tests AboutTheGameResponse with default values."""
        response = AboutTheGameResponse()
        assert response.matched_game is None
        assert response.about_the_game is None

    def test_about_the_game_response_with_values(self):
        """Tests AboutTheGameResponse with explicit values."""
        response = AboutTheGameResponse(
            matched_game="Test Game", about_the_game="Description"
        )
        assert response.matched_game == "Test Game"
        assert response.about_the_game == "Description"

    def test_similar_game_required_fields(self):
        """Tests SimilarGame requires all fields."""
        game = SimilarGame(
            name="Test Game", appid=1000, description_chunks=["chunk1", "chunk2"]
        )
        assert game.name == "Test Game"
        assert game.appid == 1000
        assert game.description_chunks == ["chunk1", "chunk2"]

    def test_find_similar_games_response_defaults(self):
        """Tests FindSimilarGamesResponse with default empty list."""
        response = FindSimilarGamesResponse()
        assert response.similar_games == []

    def test_find_similar_games_response_with_games(self):
        """Tests FindSimilarGamesResponse with games list."""
        games = [
            SimilarGame(name="Game1", appid=1000, description_chunks=["chunk"]),
            SimilarGame(name="Game2", appid=1001, description_chunks=["chunk"]),
        ]
        response = FindSimilarGamesResponse(similar_games=games)
        assert len(response.similar_games) == 2
