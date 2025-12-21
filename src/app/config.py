import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Config:
    # For security in Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Sessions Variables
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"

    # Database URL for CS50.SQL
    DATABASE_URL = f"sqlite:///{BASE_DIR / 'data' / 'users.db'}"
