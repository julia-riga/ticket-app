from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

from .database import engine, get_db, Base
from . import models, schemas, crud, auth

# Создаем таблицы в базе данных при запуске
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ticket Management System")

# Разрешаем фронтенду обращаться к бэкенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    crud.init_db(db)

@app.post("/api/login", response_model=schemas.Token)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/tickets", response_model=schemas.TicketListResponse)
def get_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
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
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    return crud.create_ticket(db, ticket)

@app.get("/api/tickets/{ticket_id}", response_model=schemas.TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
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
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if db_ticket.status == models.StatusEnum.done:
        raise HTTPException(status_code=400, detail="Cannot modify ticket with status 'done'")
    
    if ticket.status is not None and ticket.status != models.StatusEnum.done and db_ticket.status == models.StatusEnum.done:
        raise HTTPException(status_code=400, detail="Cannot change status from 'done'")
    
    return crud.update_ticket(db, ticket_id, ticket)

@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin_user)
):
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if db_ticket.status == models.StatusEnum.done:
        raise HTTPException(status_code=400, detail="Cannot delete ticket with status 'done'")
    
    crud.delete_ticket(db, ticket_id)
    return {"message": "Ticket deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)