"""Тесты API: авторизация через httpOnly-куку и CRUD заявок."""


def test_login_sets_httponly_cookie(anon):
    response = anon.post("/api/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    assert response.json() == {"username": "admin", "is_admin": True}

    set_cookie = response.headers["set-cookie"].lower()
    assert "access_token=" in set_cookie
    assert "httponly" in set_cookie


def test_login_with_wrong_password(anon):
    response = anon.post("/api/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_tickets_require_auth(anon):
    assert anon.get("/api/tickets").status_code == 401
    assert anon.get("/api/tickets/1").status_code == 401
    assert anon.post("/api/tickets", json={"title": "Без токена"}).status_code == 401
    assert anon.delete("/api/tickets/1").status_code == 401


def test_me_returns_current_user(auth):
    response = auth.get("/api/me")
    assert response.status_code == 200
    assert response.json() == {"username": "admin", "is_admin": True}


def test_bearer_header_still_supported(anon):
    token = anon.post("/api/login", json={"username": "admin", "password": "admin"}).cookies.get("access_token")
    assert token
    anon.cookies.clear()
    response = anon.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_invalid_token_rejected(anon):
    response = anon.get("/api/me", headers={"Authorization": "Bearer broken"})
    assert response.status_code == 401


def test_logout_clears_session(auth):
    assert auth.post("/api/logout").status_code == 200
    assert auth.get("/api/me").status_code == 401


def test_ticket_crud_flow(auth):
    created = auth.post("/api/tickets", json={"title": "Тестовая заявка", "description": "описание"})
    assert created.status_code == 200

    ticket = created.json()
    ticket_id = ticket["id"]
    assert ticket["status"] == "new"
    assert ticket["priority"] == "normal"
    assert ticket["created_at"] is not None
    assert ticket["updated_at"] is not None

    listing = auth.get("/api/tickets", params={"search": "Тестовая заявка"}).json()
    assert listing["items"][0]["id"] == ticket_id
    assert listing["page"] == 1

    assert auth.get(f"/api/tickets/{ticket_id}").status_code == 200
    assert auth.get("/api/tickets/9999").status_code == 404

    updated = auth.put(f"/api/tickets/{ticket_id}", json={"priority": "high"})
    assert updated.status_code == 200
    assert updated.json()["priority"] == "high"

    # Закрытую заявку нельзя ни изменить, ни удалить
    done = auth.put(f"/api/tickets/{ticket_id}", json={"status": "done"})
    assert done.status_code == 200
    assert auth.put(f"/api/tickets/{ticket_id}", json={"title": "Новое имя"}).status_code == 400
    assert auth.delete(f"/api/tickets/{ticket_id}").status_code == 400


def test_delete_ticket(auth):
    ticket_id = auth.post("/api/tickets", json={"title": "Заявка на удаление"}).json()["id"]
    assert auth.delete(f"/api/tickets/{ticket_id}").status_code == 200
    assert auth.get(f"/api/tickets/{ticket_id}").status_code == 404


def test_filters(auth):
    auth.post("/api/tickets", json={"title": "Фильтр по приоритету", "priority": "low"})
    listing = auth.get("/api/tickets", params={"priority": "low"}).json()
    assert listing["total"] >= 1
    assert all(item["priority"] == "low" for item in listing["items"])


def test_create_validation(auth):
    assert auth.post("/api/tickets", json={"title": "ab"}).status_code == 422
    assert auth.post("/api/tickets", json={"title": "Заявка", "status": "done"}).status_code == 422
    assert auth.post("/api/tickets", json={"title": "Заявка", "priority": "urgent"}).status_code == 422


def test_sort_validation(auth):
    assert auth.get("/api/tickets", params={"sort_by": "hack"}).status_code == 422
    assert auth.get("/api/tickets", params={"sort_by": "created_at", "sort_order": "asc"}).status_code == 200


def test_update_rejects_null_required_fields(auth):
    ticket_id = auth.post("/api/tickets", json={"title": "Заявка для null"}).json()["id"]
    # Обязательные поля нельзя затереть, прислав null
    assert auth.put(f"/api/tickets/{ticket_id}", json={"title": None}).status_code == 422
    assert auth.put(f"/api/tickets/{ticket_id}", json={"status": None}).status_code == 422


def test_search_is_case_insensitive(auth):
    auth.post("/api/tickets", json={"title": "Очень Важная Заявка"})
    listing = auth.get("/api/tickets", params={"search": "очень важная заявка"}).json()
    assert listing["total"] >= 1


def test_timestamps_are_marked_as_utc(auth):
    # Без метки зоны браузер трактует время как локальное и показывает его неверно
    ticket = auth.post("/api/tickets", json={"title": "Проверка времени"}).json()
    assert ticket["created_at"].endswith("+00:00")
    assert ticket["updated_at"].endswith("+00:00")
