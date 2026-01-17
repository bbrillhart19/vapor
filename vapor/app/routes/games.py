from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from loguru import logger

from vapor.app.services import GamesService
from vapor.app.deps import get_games_service

router = APIRouter(prefix="/games", tags=["games"])


class GameResponse(BaseModel):
    name: str
    appid: int


class BestMatchGame(BaseModel):
    game: GameResponse | None
    score: float | None = None


@router.get("/search", response_model=BestMatchGame, status_code=status.HTTP_200_OK)
@logger.catch
def get_game_by_name(
    name: str = Query(..., min_length=1, description="Name of game to search for"),
    svc: GamesService = Depends(get_games_service),
):
    """Find a game by searching by name, returns the best fuzzy match."""
    result = svc.best_match_by_name(name)
    if not result:
        return BestMatchGame(game=None)
    return BestMatchGame(
        game=GameResponse(
            name=result["name"],
            appid=result["appid"],
        ),
        score=result["distance"],
    )
