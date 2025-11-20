from typing import Any, Optional, Literal
from pydantic import BaseModel, Field

class PromptVariableMeta(BaseModel):
    name: str = Field(..., description="Variable name used in template")
    type: Literal["string", "text", "number", "choice"] = Field("string", description="UI input type")
    required: bool = Field(True, description="Whether the variable is mandatory")
    default: Optional[Any] = Field(None, description="Default value")
    description: Optional[str] = Field(None, description="Helper text for the user")
    choices: Optional[list[str]] = Field(None, description="Options for choice type")

class PromptSchema(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    is_enabled: bool = True

class PromptVersionSchema(BaseModel):
    version: str
    template: str
    variables_meta: Optional[list[PromptVariableMeta]] = None
    comment: Optional[str] = None
