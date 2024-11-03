from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from constants import DATABASE_URI

engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(bind=engine)
