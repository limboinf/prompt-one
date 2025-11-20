from datetime import datetime
from sqlalchemy import BigInteger, String, Text, Boolean, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Prompt(Base):
    __tablename__ = "t_prompt"
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_prompt_name_version'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment='Prompt identifier (can have multiple versions)')
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, comment='Display name')
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='Description')

    # Merged version fields
    version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False, comment='Version identifier')
    template: Mapped[str] = mapped_column(Text, nullable=False, comment='Jinja2 template content')
    variables_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='Variables metadata')
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
