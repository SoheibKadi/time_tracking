"""SQLite database setup for the agent."""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tracker.models import Base

_DB_PATH = Path(__file__).parent.parent / "agent.db"
_engine = create_engine(f"sqlite:///{_DB_PATH}", connect_args={"check_same_thread": False})
Base.metadata.create_all(_engine)

SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
