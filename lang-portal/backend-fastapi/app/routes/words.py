from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from database import get_db
from schemas import WordResponse, PaginatedResponse
from typing import List
import math

router = APIRouter(prefix="/words", tags=["Words"])

@router.get("/", response_model=PaginatedResponse[WordResponse])
def get_words(
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page"),
    per_page: int = Query(50, alias="per_page"),
    sort_by: str = Query("kanji", enum=["kanji", "romaji", "english", "correct_count", "wrong_count"]),
    order: str = Query("asc", enum=["asc", "desc"])
):
    try:
        offset = (page - 1) * per_page

        total_count = db.execute(text("SELECT COUNT(*) FROM words")).scalar()

        result = db.execute(text(f'''
            SELECT w.id, w.kanji, w.romaji, w.english, 
                   COALESCE(r.correct_count, 0) AS correct_count,
                   COALESCE(r.wrong_count, 0) AS wrong_count
            FROM words w
            LEFT JOIN word_reviews r ON w.id = r.word_id
            ORDER BY {sort_by} {order}
            LIMIT :limit OFFSET :offset
        '''), {"limit": per_page, "offset": offset})
        words = result.fetchall()

        return PaginatedResponse(
            items=[{
                "id": word.id,
                "kanji": word.kanji,
                "romaji": word.romaji,
                "english": word.english,
                "correct_count": word.correct_count,
                "wrong_count": word.wrong_count
            } for word in words],
            total=total_count,
            page=page,
            per_page=per_page,
            total_pages=math.ceil(total_count / per_page)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{word_id}", response_model=WordResponse)
def get_word(word_id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text('''
            SELECT w.id, w.kanji, w.romaji, w.english,
                   COALESCE(r.correct_count, 0) AS correct_count,
                   COALESCE(r.wrong_count, 0) AS wrong_count,
                   GROUP_CONCAT(DISTINCT g.id || '::' || g.name) as groups
            FROM words w
            LEFT JOIN word_reviews r ON w.id = r.word_id
            LEFT JOIN word_groups wg ON w.id = wg.word_id
            LEFT JOIN groups g ON wg.group_id = g.id
            WHERE w.id = :word_id
            GROUP BY w.id
        '''), {"word_id": word_id})
        word = result.fetchone()

        if not word:
            raise HTTPException(status_code=404, detail="Word not found")

        groups = []
        if word.groups:
            for group_str in word.groups.split(','):
                group_id, group_name = group_str.split('::')
                groups.append({
                    "id": int(group_id),
                    "name": group_name
                })

        return {
            "id": word.id,
            "kanji": word.kanji,
            "romaji": word.romaji,
            "english": word.english,
            "correct_count": word.correct_count,
            "wrong_count": word.wrong_count,
            "groups": groups
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
