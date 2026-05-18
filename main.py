"""
Render entrypoint: exposes the FastAPI app at module level for `uvicorn main:app`.
"""
from backend.main import app

__all__ = ["app"]
