from fastapi import APIRouter, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/status", tags=["status"])


class StatusResponse(BaseModel):
    status: str


@router.get("/health", response_model=StatusResponse, status_code=status.HTTP_200_OK)
def health_check(request: Request) -> StatusResponse:
    """Basic health check that the server is running."""
    return StatusResponse(status="alive")
