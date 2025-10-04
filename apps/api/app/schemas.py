from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class QuestionOut(BaseModel):
    id: str = Field(..., alias="id")
    source_file: Optional[str]
    source_location: Optional[str]
    category_id: Optional[str]
    category_name: Optional[str]
    auto_created_category: bool = False
    title: Optional[str]
    enunciado: str
    alternatives: Dict[str, str]
    correct_option: str
    justification: Optional[str]
    difficulty: int
    estimated_time_seconds: int
    tags: List[str] = []
    embedding: Any
    confidence: float
    duplicate: bool = False
    possible_duplicate_of: Optional[str] = None
    needs_review: bool = False
    created_by: str = "system_generated"
    created_at: str
    hash: str
    notes: Optional[str] = ""

class UploadTextRequest(BaseModel):
    filename: str
    content: str

class AttemptIn(BaseModel):
    question_id: str
    chosen_option: str

class AttemptOut(BaseModel):
    id: str
    question_id: str
    chosen_option: str
    correct: bool
    created_at: str

class StatsOut(BaseModel):
    total_attempts: int
    accuracy: float
    by_category: List[dict]