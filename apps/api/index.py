"""Vercel FastAPI entrypoint. Migrations/provisioning are explicit administrator jobs."""

from profitlens.main import app

__all__ = ["app"]
