from pydantic import BaseModel
from typing import Optional, Any

class ProfileIn(BaseModel):
    basic_info: str
    schedule_text: str
    hr_zones: Optional[str] = None
    other_info: Optional[str] = None

class AnalysisOut(BaseModel):
    summary_text: str

class PlanOut(BaseModel):
    plan_text: str
    plan_json: Optional[Any] = None
