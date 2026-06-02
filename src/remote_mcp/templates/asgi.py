"""
Production ASGI entry point for Uvicorn / Gunicorn + Uvicorn workers.

Usage:
  # Development
  uvicorn asgi:application --reload --host 127.0.0.1 --port 8001 --lifespan on

  # Production (multi-worker)
  uvicorn asgi:application --host 0.0.0.0 --port 8001 --workers 4 --lifespan on
"""

from src.app import app as application  # noqa: F401
