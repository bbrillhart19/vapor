from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/health")
def health_check(request: Request) -> JSONResponse:
    """Basic health check that the server is running."""
    return JSONResponse({"status": "alive"}, status_code=200)
