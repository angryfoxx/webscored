import os

DATABASE_URI = os.getenv("DATABASE_URI") or "sqlite:///matches.db"

CONCURRENCY_LIMIT = 5
RETRY_LIMIT = 3
