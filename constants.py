import os

DATABASE_URI = os.getenv("DATABASE_URI") or "sqlite:///matches.db"
