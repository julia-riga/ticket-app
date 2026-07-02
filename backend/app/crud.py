from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc
from . import models, schemas
from .auth import get_password_hash

def create_user(db: Session, username: str, password: str):
    hashed_password = get_password_hash(password)
    db_user = models.User(username=username, hashed_password=hashed_password)
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
        query = query.filter(
            or_(
                models.Ticket.title.contains(search),
                models.Ticket.description.contains(search)
            )
        )
    
    order_column = getattr(models.Ticket, sort_by, models.Ticket.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))
    
    total = query.count()
    tickets = query.offset(skip).limit(limit).all()
    
    return tickets, total

def create_ticket(db: Session, ticket: schemas.TicketCreate):
    db_ticket = models.Ticket(**ticket.model_dump())
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def update_ticket(db: Session, ticket_id: int, ticket: schemas.TicketUpdate):
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if db_ticket is None:
        return None
    
    update_data = ticket.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ticket, key, value)
    
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def delete_ticket(db: Session, ticket_id: int):
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if db_ticket is None:
        return None
    db.delete(db_ticket)
    db.commit()
    return db_ticket

def init_db(db: Session):
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        create_user(db, username="admin", password="admin")