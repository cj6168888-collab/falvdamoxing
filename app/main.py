"""ASGI application entrypoint."""

from app.app_factory import create_app
from app.app_factory import lifespan


app = create_app()
