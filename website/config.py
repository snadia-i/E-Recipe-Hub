from __future__ import annotations

import os
from pathlib import Path


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    # Vercel Functions accept request bodies up to 4.5 MB. Keep uploads below that.
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    DATABASE_URL = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("NEON_DATABASE_URL")
        or ""
    ).strip()
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "database2.db")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    DEFAULT_RECIPE_IMAGE = "/static/images/AyamGorengBerempah-1260.jpg"
    DEFAULT_PROFILE_IMAGE = "/static/images/mingyu.jpg"
    DEFAULT_HEADER_IMAGE = "/static/images/view.jpg"
    IS_VERCEL = bool(os.environ.get("VERCEL"))


def database_path(instance_path: str, database_name: str) -> Path:
    return Path(instance_path) / database_name
