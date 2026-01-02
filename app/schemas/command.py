from pydantic import BaseModel
from typing import Optional, Any, Dict, List


class CommandInput(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None


class ParsedIntent(BaseModel):
    action: str
    entity: Optional[str] = None
    parameters: Dict[str, Any] = {}
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None


class CommandResponse(BaseModel):
    success: bool
    action: str
    message: str
    data: Optional[Any] = None
    requires_confirmation: bool = False
    confirmation_id: Optional[str] = None


class MultiStepPlan(BaseModel):
    steps: List[ParsedIntent]
    current_step: int = 0
    status: str = "pending"
