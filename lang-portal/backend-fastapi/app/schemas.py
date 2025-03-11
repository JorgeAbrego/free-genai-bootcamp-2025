from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Generic, TypeVar, List, TypeVar

T = TypeVar("T")

class GroupResponse(BaseModel):
    id: int
    name: str
    words_count: int

    class Config:
        from_attributes = True


class StudyActivityResponse(BaseModel):
    id: int
    name: str
    url: str
    preview_url: Optional[str] = None

    class Config:
        from_attributes = True


class StudySessionResponse(BaseModel):
    id: int
    group_id: int
    group_name: str
    activity_id: int
    activity_name: str
    start_time: datetime
    end_time: datetime
    review_items_count: int

    class Config:
        from_attributes = True
    
    
class WordGroupResponse(BaseModel):
    word_id: int
    group_id: int

    class Config:
        from_attributes = True


class WordReviewItemResponse(BaseModel):
    id: int
    word_id: int
    study_session_id: int
    result: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WordReviewResponse(BaseModel):
    id: int
    word_id: int
    correct_count: int
    wrong_count: int
    last_reviewed: datetime

    class Config:
        from_attributes = True


class WordResponse(BaseModel):
    id: int
    kanji: str
    romaji: str
    english: str
    correct_count: int
    wrong_count: int
    groups: Optional[List[dict]] = None

    class Config:
        from_attributes = True
        

class RecentSessionResponse(BaseModel):
    id: int
    group_id: int
    activity_name: str
    created_at: datetime
    correct_count: int
    wrong_count: int

    class Config:
        from_attributes = True

class StudyStatsResponse(BaseModel):
    total_vocabulary: int
    total_words_studied: int
    mastered_words: int
    success_rate: float
    total_sessions: int
    active_groups: int
    current_streak: int

    class Config:
        from_attributes = True
        
        
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int

    class Config:
        from_attributes = True
        
class StudySessionCreateRequest(BaseModel):
    group_id: int
    study_activity_id: int

class ReviewLogRequest(BaseModel):
    word_id: int
    correct: bool