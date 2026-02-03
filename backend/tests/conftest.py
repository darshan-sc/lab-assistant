"""
Shared test fixtures for the ResearchNexus backend.

How it works:
- An in-memory SQLite database is used so tests run fast and don't need Postgres.
- Each test gets a fresh DB session that is rolled back after the test.
- The FastAPI TestClient has the auth dependency overridden so you don't need
  a real Supabase JWT — every request acts as `mock_user`.

To run tests:
    cd backend
    pip install -r requirements-dev.txt
    pytest
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.models.base import Base
from app.models.user import User
from app.db import get_db
from app.deps import get_current_user
from app.main import app


# ---------------------------------------------------------------------------
# In-memory SQLite engine
# ---------------------------------------------------------------------------
# We use "check_same_thread=False" because FastAPI's TestClient may access
# the DB from a different thread than the one that created it.
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SQLite doesn't enforce foreign keys by default — turn them on so our
# constraints behave like Postgres.
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _setup_db():
    """Create all tables before each test and drop them after.

    This gives every test a completely clean database.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def test_db() -> Session:
    """Yield a SQLAlchemy session connected to the in-memory SQLite DB.

    Usage in a test:
        def test_something(test_db):
            test_db.add(MyModel(...))
            test_db.commit()
            assert test_db.query(MyModel).count() == 1
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def mock_user(test_db: Session) -> User:
    """Insert and return a fake user for auth bypass.

    The `client` fixture overrides `get_current_user` to return this user,
    so every authenticated endpoint will see this user without needing a JWT.
    """
    user = User(supabase_uid="test-uid-000", email="test@example.com")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture()
def client(test_db: Session, mock_user: User) -> TestClient:
    """FastAPI TestClient with DB and auth overridden.

    Usage in a test:
        def test_list_projects(client):
            resp = client.get("/projects")
            assert resp.status_code == 200

    The dependency overrides ensure:
    - `get_db` returns the in-memory test session.
    - `get_current_user` returns `mock_user` (no JWT needed).
    """

    def _override_get_db():
        try:
            yield test_db
        finally:
            pass  # session is closed by the test_db fixture

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with TestClient(app) as tc:
        yield tc

    # Clean up overrides so they don't leak between tests
    app.dependency_overrides.clear()
