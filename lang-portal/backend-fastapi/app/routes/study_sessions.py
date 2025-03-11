from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from database import get_db
from schemas import StudySessionResponse, PaginatedResponse, WordResponse, StudySessionCreateRequest, ReviewLogRequest
from typing import List
import math

router = APIRouter(prefix="/study-sessions", tags=["Study Sessions"])

@router.get("/", response_model=PaginatedResponse[StudySessionResponse])
def get_study_sessions(
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page"),
    per_page: int = Query(10, alias="per_page")
):
    try:
        offset = (page - 1) * per_page

        total_count = db.execute(text('''
            SELECT COUNT(*) FROM study_sessions
        ''')) .scalar()
        
        result = db.execute(text('''
            SELECT 
                ss.id, ss.group_id, g.name as group_name,
                sa.id as activity_id, sa.name as activity_name,
                ss.created_at, COUNT(wri.id) as review_items_count
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            GROUP BY ss.id
            ORDER BY ss.created_at DESC
            LIMIT :limit OFFSET :offset
        '''), {"limit": per_page, "offset": offset})
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


@router.get("/{id}", response_model=StudySessionResponse)
def get_study_session(id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text('''
            SELECT 
                ss.id, ss.group_id, g.name as group_name,
                sa.id as activity_id, sa.name as activity_name,
                ss.created_at, COUNT(wri.id) as review_items_count
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            WHERE ss.id = :id
            GROUP BY ss.id
        '''), {"id": id})
        session = result.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Study session not found")
        
        return {
            "id": session.id,
            "group_id": session.group_id,
            "group_name": session.group_name,
            "activity_id": session.activity_id,
            "activity_name": session.activity_name,
            "start_time": session.created_at,
            "end_time": session.created_at,
            "review_items_count": session.review_items_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
def reset_study_sessions(db: Session = Depends(get_db)):
    try:
        db.execute(text('DELETE FROM word_review_items'))
        db.execute(text('DELETE FROM study_sessions'))
        db.commit()
        
        return {"message": "Study history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Adding left endpoints 
@router.post("/", status_code=201)
def create_study_session(data: StudySessionCreateRequest, db: Session = Depends(get_db)):
    try:
        group_check = db.execute(text("SELECT id FROM groups WHERE id = :group_id"), {"group_id": data.group_id}).fetchone()
        if not group_check:
            raise HTTPException(status_code=404, detail="Group not found")

        activity_check = db.execute(text("SELECT id FROM study_activities WHERE id = :study_activity_id"), 
                                    {"study_activity_id": data.study_activity_id}).fetchone()
        if not activity_check:
            raise HTTPException(status_code=404, detail="Study activity not found")

        result = db.execute(text('''
            INSERT INTO study_sessions (group_id, study_activity_id, created_at)
            VALUES (:group_id, :study_activity_id, :created_at)
        '''), {
            "group_id": data.group_id,
            "study_activity_id": data.study_activity_id,
            "created_at": datetime.now()
        })
        db.commit()

        return {"session_id": result.lastrowid}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/review")
def log_review(id: int, data: ReviewLogRequest, db: Session = Depends(get_db)):
    try:
        word_check = db.execute(text("SELECT id FROM words WHERE id = :word_id"), {"word_id": data.word_id}).fetchone()
        if not word_check:
            raise HTTPException(status_code=404, detail="Word not found")

        session_check = db.execute(text("SELECT id FROM study_sessions WHERE id = :id"), {"id": id}).fetchone()
        if not session_check:
            raise HTTPException(status_code=404, detail="Study session not found")

        db.execute(text('''
            INSERT INTO word_review_items (word_id, correct, study_session_id)
            VALUES (:word_id, :correct, :study_session_id)
        '''), {
            "word_id": data.word_id,
            "correct": data.correct,
            "study_session_id": id
        })

        review_check = db.execute(text("SELECT * FROM word_reviews WHERE word_id = :word_id"), 
                                  {"word_id": data.word_id}).fetchone()

        if review_check:
            if data.correct:
                db.execute(text('''
                    UPDATE word_reviews 
                    SET correct_count = correct_count + 1, last_reviewed = :last_reviewed 
                    WHERE word_id = :word_id
                '''), {"last_reviewed": datetime.now(), "word_id": data.word_id})
            else:
                db.execute(text('''
                    UPDATE word_reviews 
                    SET wrong_count = wrong_count + 1, last_reviewed = :last_reviewed 
                    WHERE word_id = :word_id
                '''), {"last_reviewed": datetime.now(), "word_id": data.word_id})
        else:
            db.execute(text('''
                INSERT INTO word_reviews (word_id, correct_count, wrong_count, last_reviewed)
                VALUES (:word_id, :correct_count, :wrong_count, :last_reviewed)
            '''), {
                "word_id": data.word_id,
                "correct_count": 1 if data.correct else 0,
                "wrong_count": 0 if data.correct else 1,
                "last_reviewed": datetime.now()
            })

        db.commit()
        return {"message": "Review logged successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))