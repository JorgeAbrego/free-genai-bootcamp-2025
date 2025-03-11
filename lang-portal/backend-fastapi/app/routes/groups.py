from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from database import get_db
from schemas import GroupResponse, WordResponse, StudySessionResponse
from typing import List, Optional
import json

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.get("/", response_model=List[GroupResponse])
def get_groups(
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page"),
    sort_by: str = Query("name", regex="^(name|words_count)$"),
    order: str = Query("asc", regex="^(asc|desc)$")
):
    try:
        groups_per_page = 10
        offset = (page - 1) * groups_per_page

        result = db.execute(text(f'''
            SELECT id, name, words_count
            FROM groups
            ORDER BY {sort_by} {order}
            LIMIT :limit OFFSET :offset
        '''), {"limit": groups_per_page, "offset": offset})
        groups = result.fetchall()

        total_groups = db.execute(text('SELECT COUNT(*) FROM groups')).scalar()
        total_pages = (total_groups + groups_per_page - 1) // groups_per_page

        return [{
            "id": group.id,
            "name": group.name,
            "words_count": group.words_count
        } for group in groups]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}", response_model=GroupResponse)
def get_group(id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text('''SELECT id, name, words_count FROM groups WHERE id = :id'''), {"id": id})
        group = result.fetchone()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return group
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/words", response_model=List[WordResponse])
def get_group_words(
    id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page"),
    sort_by: str = Query("kanji", regex="^(kanji|romaji|english|correct_count|wrong_count)$"),
    order: str = Query("asc", regex="^(asc|desc)$")
):
    try:
        words_per_page = 10
        offset = (page - 1) * words_per_page

        # Check if group exists
        group_check = db.execute(text('SELECT name FROM groups WHERE id = :id'), {"id": id}).fetchone()
        if not group_check:
            raise HTTPException(status_code=404, detail="Group not found")

        result = db.execute(text(f'''
            SELECT w.*, COALESCE(wr.correct_count, 0) as correct_count, COALESCE(wr.wrong_count, 0) as wrong_count
            FROM words w
            JOIN word_groups wg ON w.id = wg.word_id
            LEFT JOIN word_reviews wr ON w.id = wr.word_id
            WHERE wg.group_id = :id
            ORDER BY {sort_by} {order}
            LIMIT :limit OFFSET :offset
        '''), {"id": id, "limit": words_per_page, "offset": offset})
        words = result.fetchall()

        total_words = db.execute(text('SELECT COUNT(*) FROM word_groups WHERE group_id = :id'), {"id": id}).scalar()
        total_pages = (total_words + words_per_page - 1) // words_per_page

        return [{
            "id": word.id,
            "kanji": word.kanji,
            "romaji": word.romaji,
            "english": word.english,
            "correct_count": word.correct_count,
            "wrong_count": word.wrong_count
        } for word in words]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/study_sessions", response_model=List[StudySessionResponse])
def get_group_study_sessions(
    id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page"),
    sort_by: str = Query("created_at", regex="^(created_at|last_activity_time|activity_name|group_name|review_items_count)$"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    try:
        sessions_per_page = 10
        offset = (page - 1) * sessions_per_page

        result = db.execute(text(f'''
            SELECT 
                s.id, s.group_id, s.study_activity_id, s.created_at as start_time,
                (
                    SELECT MAX(created_at) FROM word_review_items WHERE study_session_id = s.id
                ) as last_activity_time,
                a.name as activity_name, g.name as group_name,
                (
                    SELECT COUNT(*) FROM word_review_items WHERE study_session_id = s.id
                ) as review_count
            FROM study_sessions s
            JOIN study_activities a ON s.study_activity_id = a.id
            JOIN groups g ON s.group_id = g.id
            WHERE s.group_id = :id
            ORDER BY {sort_by} {order}
            LIMIT :limit OFFSET :offset
        '''), {"id": id, "limit": sessions_per_page, "offset": offset})
        sessions = result.fetchall()

        total_sessions = db.execute(text('SELECT COUNT(*) FROM study_sessions WHERE group_id = :id'), {"id": id}).scalar()
        total_pages = (total_sessions + sessions_per_page - 1) // sessions_per_page

        sessions_data = []
        for session in sessions:
            end_time = session.last_activity_time or db.execute(text('SELECT datetime(:start, "+30 minutes")'), {"start": session.start_time}).scalar()
            sessions_data.append({
                "id": session.id,
                "group_id": session.group_id,
                "group_name": session.group_name,
                "study_activity_id": session.study_activity_id,
                "activity_name": session.activity_name,
                "start_time": session.start_time,
                "end_time": end_time,
                "review_items_count": session.review_count
            })
        
        return sessions_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Adding left endpoint 
@router.get("/{id}/words/raw")
def get_group_words_raw(id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT name FROM groups WHERE id = :id"), {"id": id})
        group = result.fetchone()
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        result = db.execute(text('''
            SELECT g.id as group_id, g.name as group_name, w.*
            FROM groups g
            JOIN word_groups wg ON g.id = wg.group_id
            JOIN words w ON w.id = wg.word_id
            WHERE g.id = :id
        '''), {"id": id})
        
        data = result.fetchall()

        response = {
            "group_id": id,
            "group_name": data[0].group_name if data else group.name,
            "words": []
        }

        for row in data:
            word = {
                "id": row.id,
                "kanji": row.kanji,
                "romaji": row.romaji,
                "english": row.english,
                "parts": json.loads(row.parts) if row.parts else []
            }
            response["words"].append(word)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))