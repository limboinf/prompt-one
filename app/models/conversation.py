from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Conversation(Base):
    __tablename__ = "t_conversation"
    __table_args__ = (
        Index('idx_prompt_id', 'prompt_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_prompt_version', 'prompt_id', 'version'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Prompt reference
    prompt_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='Reference to prompt id')
    version: Mapped[str] = mapped_column(String(32), nullable=False, comment='Prompt version used')

    # Conversation data
    user_input: Mapped[str] = mapped_column(Text, nullable=False, comment='User input/question')
    ai_response: Mapped[str] = mapped_column(Text, nullable=False, comment='AI generated response')

    # Variables used in the prompt template
    template_variables: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='Variables used to render the prompt template')

    # Rendered prompt (the actual prompt sent to AI after template rendering)
    rendered_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, comment='Rendered prompt sent to AI')

    # Metadata
    model_name: Mapped[str | None] = mapped_column(String(64), nullable=True, comment='AI model used (e.g., gpt-4, claude-3)')
    temperature: Mapped[float | None] = mapped_column(nullable=True, comment='Temperature parameter used')
    tokens_used: Mapped[int | None] = mapped_column(nullable=True, comment='Total tokens consumed')

    # Additional metadata
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='Additional metadata (e.g., response time, cost, etc.)')

    # User tracking
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, comment='User identifier')
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, comment='Session identifier for grouping related conversations')

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
