from pydantic import BaseModel
from typing import Optional


class ChatMessage(BaseModel):
    message: str
    patient_id: Optional[int] = None   # optional: gives AI patient context


class ChatResponse(BaseModel):
    reply: str
    model_used: str