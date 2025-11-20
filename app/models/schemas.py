from typing import Any, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Conversation Schemas
class ConversationCreate(BaseModel):
    """Schema for creating a new conversation record."""
    prompt_id: int = Field(..., description="Reference to prompt id")
    version: str = Field(..., description="Prompt version used")
    user_input: str = Field(..., description="User input/question")
    ai_response: str = Field(..., description="AI generated response")
    template_variables: Optional[dict[str, Any]] = Field(None, description="Variables used to render the prompt template")
    rendered_prompt: Optional[str] = Field(None, description="Rendered prompt sent to AI")
    model_name: Optional[str] = Field(None, description="AI model used")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature parameter used")
    tokens_used: Optional[int] = Field(None, ge=0, description="Total tokens consumed")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")


class ConversationResponse(ConversationCreate):
    """Schema for conversation response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationQuery(BaseModel):
    """Schema for querying conversations."""
    prompt_id: Optional[int] = None
    version: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    model_name: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")
    offset: int = Field(0, ge=0, description="Number of records to skip")
