from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class User(BaseModel):
    id: int
    mode: str = "friendly"           # strict | friendly
    free_used_week: int = 0
    week_start: Optional[str] = None
    subscription_end: Optional[str] = None
    paid: bool = False
    vision_model: str = "gemini"     # gemini | nemotron (из первого бота)
    history: List[Dict[str, str]] = []

class Subscription(BaseModel):
    user_id: int
    expires: datetime