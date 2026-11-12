from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import auth, crud, models, schemas
from .config import settings
from .database import Base, SessionLocal, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем таблицы и демо-администратора при запуске
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        crud.init_db(db)
    yield


app = FastAPI(title="Ticket Management System", lifespan=lifespan)

# Разрешаем фронтенду обращаться к бэкенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/login", response_model=schemas.UserResponse)
def login(login_data: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # Токен кладем в httpOnly-куку: JS его не видит, значит XSS его не украдет
    access_token = auth.create_access_token(data={"sub": user.username})
    response.set_cookie(
        key=auth.COOKIE_NAME,
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    return user


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(key=auth.COOKIE_NAME, path="/")
    return {"message": "Logged out"}


@app.get("/api/me", response_model=schemas.UserResponse)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.get("/api/tickets", response_model=schemas.TicketListResponse)
def get_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[schemas.StatusEnum] = None,
    priority: Optional[schemas.PriorityEnum] = None,
    search: Optional[str] = None,
    sort_by: Literal["created_at", "updated_at", "title", "status", "priority", "id"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    skip = (page - 1) * page_size
    tickets, total = crud.get_tickets(
        db, skip=skip, limit=page_size,
        status=status, priority=priority, search=search,
        sort_by=sort_by, sort_order=sort_order
    )
    return {
        "items": tickets,
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size
    }


@app.post("/api/tickets", response_model=schemas.TicketResponse)
def create_ticket(
    ticket: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.create_ticket(db, ticket)


@app.get("/api/tickets/{ticket_id}", response_model=schemas.TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.put("/api/tickets/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket: schemas.TicketUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_ticket = crud.get_ticket(db, ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if db_ticket.status == models.StatusEnum.done:
        raise HTTPException(status_code=400, detail="Cannot modify ticket with status 'done'")

    return crud.update_ticket(db, db_ticket, ticket)


@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin_user)
):
    db_ticket = crud.get_ticket(db, ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if db_ticket.status == models.StatusEnum.done:
        raise HTTPException(status_code=400, detail="Cannot delete ticket with status 'done'")

    crud.delete_ticket(db, db_ticket)
    return {"message": "Ticket deleted successfully"}


# Собранный фронтенд (frontend/dist) отдаем тем же сервисом, что и API:
# на проде это дает один домен без CORS. Папки может не быть при локальной
# разработке (фронтенд запускается отдельно через Vite) — тогда пропускаем.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
