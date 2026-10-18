# File: application/src/app/models/password_reset.py
from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime, timedelta, timezone

def get_pakistan_time() -> datetime:
    """Get current time in Pakistan timezone (UTC+5)."""
    return datetime.now(timezone(timedelta(hours=5)))

class PasswordReset(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    pin: str = Field(nullable=False, description="6-digit reset PIN")
    created_at: datetime = Field(default_factory=get_pakistan_time)
    expires_at: datetime = Field(
        default_factory=lambda: get_pakistan_time() + timedelta(minutes=15)
    )
    used: bool = Field(default=False)