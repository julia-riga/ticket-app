import os
import tempfile
from pathlib import Path

# Подменяем базу на тестовую до импорта настроек приложения.
# Переменные окружения имеют приоритет над backend/.env
TEST_DB = Path(tempfile.gettempdir()) / "ticket_app_test.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = "sqlite:///" + TEST_DB.as_posix()
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def anon(client):
    """Клиент без авторизации."""
    client.cookies.clear()
    return client


@pytest.fixture
def auth(anon):
    """Клиент с валидной сессией (демо-администратор)."""
    response = anon.post("/api/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return anon
