# 🎫 Ticket Management System

> Fullstack-приложение для учёта и управления внутренними заявками.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript)

---

##  О проекте

Ticket Management System — это современное fullstack-приложение для создания, отслеживания и управления внутренними заявками. Разработано с использованием **FastAPI** на backend и **React + TypeScript** на frontend.

### ✨ Возможности

- 🔐 Авторизация с JWT-токенами
- 📝 CRUD-операции для заявок
-  Поиск и фильтрация по статусу, приоритету и тексту
- 📊 Сортировка по дате создания и приоритету
- 📄 Пагинация списка заявок
- 🎨 Современный UI с градиентным дизайном
- ✅ Валидация данных на frontend и backend
- 🛡️ Бизнес-правила для защиты данных

---

## 🛠 Стек технологий

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy + SQLite
- JWT (python-jose)
- Pydantic
- Uvicorn

**Frontend:**
- React 18
- TypeScript
- Axios
- Vite

---

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11 или выше
- Node.js 18 или выше

### Установка и запуск Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main

Backend будет доступен по адресу: http://localhost:8000
📚 API документация (Swagger UI): http://localhost:8000/docs

Установка и запуск Frontend
cd frontend
npm install
npm run dev

Frontend будет доступен по адресу: http://localhost:5173

🔐 Авторизация
| Поле | Значение |
|------|----------|
| Логин | admin |
| Пароль | admin |
⚠️ Только администратор может удалять заявки.

📖 API Endpoints
Авторизация:
POST /api/login — Вход в систему
Заявки:
GET /api/tickets — Получить список заявок
POST /api/tickets — Создать заявку
GET /api/tickets/{id} — Получить заявку по ID
PUT /api/tickets/{id} — Обновить заявку
DELETE /api/tickets/{id} — Удалить заявку (только admin)

Параметры для GET /api/tickets
?page=1              # Номер страницы (по умолчанию: 1)
&page_size=10        # Размер страницы (по умолчанию: 10)
&status=new          # Фильтр по статусу
&priority=high       # Фильтр по приоритету
&search=текст        # Поиск по названию и описанию
&sort_by=created_at  # Сортировка по полю
&sort_order=desc     # Порядок сортировки (asc/desc)

📊 Модель данных
Заявка (Ticket)
id (int) — Уникальный идентификатор
title (string) — Заголовок (3-120 символов)
description (string) — Описание (до 1000 символов)
status (enum) — Статус: new, in_progress, done
priority (enum) — Приоритет: low, normal, high
created_at (datetime) — Дата создания (UTC)
updated_at (datetime) — Дата последнего изменения (UTC)

📁 Структура проекта
ticket-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # Точка входа приложения
│   │   ├── models.py        # Модели базы данных
│   │   ├── schemas.py       # Pydantic схемы
│   │   ├── database.py      # Настройка БД
│   │   ├── crud.py          # Операции с БД
│   │   ── auth.py          # Авторизация
│   └── requirements.txt     # Зависимости Python
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Главный компонент
│   │   ├── App.css          # Стили
│   │   ├── api.ts           # API клиент
│   │   ├── types.ts         # TypeScript типы
│   │   └── main.tsx         # Точка входа
│   └── package.json         # Зависимости Node
│
└── README.md