"""Shared pytest fixtures."""
import shutil
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.services.indexer import SkillIndexer

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_REPO = FIXTURES / "sample-repo"

_TEST_DB = "sqlite:///./test_skills.db"
_test_engine = create_engine(_TEST_DB, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=_test_engine, autoflush=False, autocommit=False, future=True)

# Ensure tables exist at module load.
Base.metadata.create_all(bind=_test_engine)


@pytest.fixture
def sample_repo() -> Path:
    """Return the path to the bundled sample repo fixture."""
    return SAMPLE_REPO


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Copy the sample repo into a temporary directory for mutation tests."""
    repo = tmp_path / "skills-repo"
    shutil.copytree(SAMPLE_REPO, repo)
    return repo


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a fresh test database session for each test that needs one."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Clean all data between tests.
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture
def indexer(db_session: Session) -> SkillIndexer:
    """Provide a SkillIndexer bound to the test database."""
    return SkillIndexer(db_session)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with DB and indexer dependencies overridden."""
    from app.main import app as fastapi_app

    def _override_db() -> Generator[Session, None, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_db

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()