from fastapi import FastAPI

from vapor.app.factory import create_app


def test_create_app():
    """Tests the `create_app` start up process for Vapor application layer."""
    app = create_app()
    assert isinstance(app, FastAPI)
    assert app.title == "Vapor API"


def test_create_app_includes_status_router():
    """Tests that the status router is included in the app."""
    app = create_app()
    # Check that the status routes are registered
    routes = [route.path for route in app.routes]
    assert "/status/health" in routes
