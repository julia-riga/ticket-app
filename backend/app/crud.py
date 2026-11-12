from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc, func, inspect, text
from . import models, schemas
from .auth import get_password_hash
from .config import settings

def create_user(db: Session, username: str, password: str, is_admin: bool = False):
    hashed_password = get_password_hash(password)
    db_user = models.User(username=username, hashed_password=hashed_password, is_admin=is_admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_tickets(db: Session, skip=0, limit=10, status=None, priority=None, search=None, sort_by="created_at", sort_order="desc"):
    query = db.query(models.Ticket)
    
    if status:
        query = query.filter(models.Ticket.status == status)
    if priority:
        query = query.filter(models.Ticket.priority == priority)
    if search:
        # py_lower — своя функция SQLite (см. database.py): регистронезависимый
        # поиск по русскому тексту, который обычный LIKE в SQLite не умеет
        pattern = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.py_lower(models.Ticket.title).like(pattern),
                func.py_lower(models.Ticket.description).like(pattern)
            )
        )
    
    order_column = getattr(models.Ticket, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))
    
    total = query.count()
    tickets = query.offset(skip).limit(limit).all()
    
    return tickets, total

def get_ticket(db: Session, ticket_id: int):
    return db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

def create_ticket(db: Session, ticket: schemas.TicketCreate):
    db_ticket = models.Ticket(**ticket.model_dump())
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def update_ticket(db: Session, db_ticket: models.Ticket, ticket: schemas.TicketUpdate):
    update_data = ticket.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ticket, key, value)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def delete_ticket(db: Session, db_ticket: models.Ticket):
    db.delete(db_ticket)
    db.commit()
    return db_ticket

def init_db(db: Session):
    migrate_schema(db)

    admin = db.query(models.User).filter(models.User.username == settings.admin_username).first()
    if admin is None:
        create_user(db, username=settings.admin_username, password=settings.admin_password, is_admin=True)
    elif not admin.is_admin:
        admin.is_admin = True
        db.commit()


def migrate_schema(db: Session):
    # create_all() не меняет уже существующие таблицы, поэтому недостающие
    # колонки и данные правим вручную. Для демо-SQLite этого достаточно.
    inspector = inspect(db.get_bind())
    tables = set(inspector.get_table_names())

    if "users" in tables and "is_admin" not in {c["name"] for c in inspector.get_columns("users")}:
        db.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
        db.commit()

    if "tickets" in tables:
        # Раньше updated_at оставался NULL до первого изменения заявки.
        # Проверяем наличие таких строк, чтобы не писать в БД на каждом старте
        has_empty_updated_at = db.execute(
            text("SELECT 1 FROM tickets WHERE updated_at IS NULL LIMIT 1")
        ).first()
        if has_empty_updated_at:
            db.execute(text("UPDATE tickets SET updated_at = created_at WHERE updated_at IS NULL"))
            db.commit()