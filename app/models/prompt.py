from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

class Prompt(Base):
    __tablename__ = "t_prompt"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment='Unique identifier')
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, comment='Display name')
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment='Description')
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    versions: Mapped[List["PromptVersion"]] = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan")

class PromptVersion(Base):
    __tablename__ = "t_prompt_version"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("t_prompt.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, comment='Version identifier')
    template: Mapped[str] = mapped_column(Text, nullable=False, comment='Jinja2 template content')
    variables_meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment='Variables metadata')
    is_latest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="versions")

    __table_args__ = (
        UniqueConstraint('prompt_id', 'version', name='uk_prompt_version'),
    )
