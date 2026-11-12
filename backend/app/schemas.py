from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

from .models import PriorityEnum, StatusEnum


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    description: Optional[str] = Field(None, max_length=1000)
    status: StatusEnum = StatusEnum.new
    priority: PriorityEnum = PriorityEnum.normal

    @field_validator("status")
    @classmethod
    def status_must_not_be_done(cls, value: StatusEnum) -> StatusEnum:
        # Заявку со статусом done нельзя ни изменить, ни удалить,
        # поэтому создавать ее сразу закрытой нельзя
        if value is StatusEnum.done:
            raise ValueError("Нельзя создать заявку сразу со статусом 'done'")
        return value


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=120)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data):
        # Поля в БД объявлены NOT NULL: если пришел явный null, запрос упал бы
        # с IntegrityError и вернул 500. Лучше сразу ответить 422.
        # description можно очистить, поэтому его здесь нет.
        if isinstance(data, dict):
            for field in ("title", "status", "priority"):
                if field in data and data[field] is None:
                    raise ValueError(f"Поле '{field}' не может быть null")
        return data


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: StatusEnum
    priority: PriorityEnum
    created_at: datetime
    updated_at: Optional[datetime]

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        # SQLite хранит время как UTC, но без смещения. Без явной метки зоны
        # браузер посчитает его локальным и покажет неверно, поэтому помечаем UTC
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class TicketListResponse(BaseModel):
    items: List[TicketResponse]
    total: int
    page: int
    pages: int


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    is_admin: bool
