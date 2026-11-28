"""
Test fixtures and database setup.

Creates an isolated test database, provides test
sessions and FastAPI clients, and mocks external
dependencies such as email sending.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.routers import auth

test_url = make_url(settings.database_url).set(database="todo_test")
assert test_url.database == "todo_test"

test_engine = create_engine(test_url)
TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE email_codes, users CASCADE"))


@pytest.fixture
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sent_codes(monkeypatch):
    sent = []

    def fake_send(to_email, name, code):
        sent.append({"email": to_email, "code": code})

    monkeypatch.setattr(auth, "send_verification_code", fake_send)
    return sent


@pytest.fixture
def client(sent_codes):
    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()