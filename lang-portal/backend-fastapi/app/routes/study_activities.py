from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from database import get_db
from schemas import StudyActivityResponse, StudySessionResponse, PaginatedResponse
from typing import List, Optional
import math

router = APIRouter(prefix="/study-activities", tags=["Study Activities"])

@router.get("/", response_model=List[StudyActivityResponse])
def get_study_activities(db: Session = Depends(get_db)):
    try:
        result = db.execute(text('SELECT id, name, url, preview_url FROM study_activities'))
        activities = result.fetchall()
        
        return [{
            "id": activity.id,
            "name": activity.name,
            "url": activity.url,
            "preview_url": activity.preview_url
        } for activity in activities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}", response_model=StudyActivityResponse)
def get_study_activity(id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text('SELECT id, name, url, preview_url FROM study_activities WHERE id = :id'), {"id": id})
        activity = result.fetchone()
        
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        return activity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/sessions", response_model=PaginatedResponse[StudySessionResponse])
def get_study_activity_sessions(
    id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page"),
    per_page: int = Query(10, alias="per_page")
):
    try:
        offset = (page - 1) * per_page

        # Verify activity exists
        activity_check = db.execute(text('SELECT id FROM study_activities WHERE id = :id'), {"id": id}).fetchone()
        if not activity_check:
            raise HTTPException(status_code=404, detail="Activity not found")

        total_count = db.execute(text('''
            SELECT COUNT(*) FROM study_sessions WHERE study_activity_id = :id
        '''), {"id": id}).scalar()
        
        result = db.execute(text('''
            SELECT 
                ss.id, ss.group_id, g.name as group_name, sa.name as activity_name, 
                ss.created_at, ss.study_activity_id as activity_id,
                COUNT(wri.id) as review_items_count
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            WHERE ss.study_activity_id = :id
            GROUP BY ss.id, ss.group_id, g.name, sa.name, ss.created_at, ss.study_activity_id
            ORDER BY ss.created_at DESC
            LIMIT :limit OFFSET :offset
        '''), {"id": id, "limit": per_page, "offset": offset})
        sessions = result.fetchall()

        return PaginatedResponse(
            items=[{
                "id": session.id,
                "group_id": session.group_id,
                "group_name": session.group_name,
                "activity_id": session.activity_id,
                "activity_name": session.activity_name,
                "start_time": session.created_at,
                "end_time": session.created_at,
                "review_items_count": session.review_items_count
            } for session in sessions],
            total=total_count,
            page=page,
            per_page=per_page,
            total_pages=math.ceil(total_count / per_page)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/launch")
def get_study_activity_launch_data(id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text('SELECT id, name, url, preview_url FROM study_activities WHERE id = :id'), {"id": id})
        activity = result.fetchone()
        
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        groups_result = db.execute(text('SELECT id, name FROM groups'))
        groups = groups_result.fetchall()
        
        return {
            "activity": {
                "id": activity.id,
                "name": activity.name,
                "url": activity.url,
                "preview_url": activity.preview_url
            },
            "groups": [{
                "id": group.id,
                "name": group.name
            } for group in groups]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
