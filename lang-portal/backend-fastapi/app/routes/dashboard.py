from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from database import get_db
from datetime import datetime
from schemas import RecentSessionResponse, StudyStatsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/recent-session", response_model=RecentSessionResponse | None)
def get_recent_session(db: Session = Depends(get_db)):
    try:
        result = db.execute(text('''
            SELECT 
                ss.id,
                ss.group_id,
                sa.name as activity_name,
                ss.created_at,
                COUNT(CASE WHEN wri.correct = 1 THEN 1 END) as correct_count,
                COUNT(CASE WHEN wri.correct = 0 THEN 1 END) as wrong_count
            FROM study_sessions ss
            JOIN study_activities sa ON ss.study_activity_id = sa.id
            LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            GROUP BY ss.id
            ORDER BY ss.created_at DESC
            LIMIT 1
        '''))
        session = result.fetchone()
        
        if not session:
            return None
        
        return RecentSessionResponse(
            id=session.id,
            group_id=session.group_id,
            activity_name=session.activity_name,
            created_at=session.created_at,
            correct_count=session.correct_count,
            wrong_count=session.wrong_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StudyStatsResponse)
def get_study_stats(db: Session = Depends(get_db)):
    try:
        total_vocabulary = db.execute(text('SELECT COUNT(*) FROM words')).scalar()
        total_words = db.execute(text('''
            SELECT COUNT(DISTINCT word_id)
            FROM word_review_items
            JOIN study_sessions ON word_review_items.study_session_id = study_sessions.id
        ''')).scalar()
        mastered_words = db.execute(text('''
            WITH word_stats AS (
                SELECT 
                    word_id,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
                FROM word_review_items
                JOIN study_sessions ON word_review_items.study_session_id = study_sessions.id
                GROUP BY word_id
                HAVING total_attempts >= 5
            )
            SELECT COUNT(*) FROM word_stats WHERE success_rate >= 0.8
        ''')).scalar()
        success_rate = db.execute(text('''
            SELECT SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
            FROM word_review_items
            JOIN study_sessions ON word_review_items.study_session_id = study_sessions.id
        ''')).scalar() or 0
        total_sessions = db.execute(text('SELECT COUNT(*) FROM study_sessions')).scalar()
        active_groups = db.execute(text('''
            SELECT COUNT(DISTINCT group_id)
            FROM study_sessions
            WHERE created_at >= date('now', '-30 days')
        ''')).scalar()
        current_streak = db.execute(text('''
            WITH daily_sessions AS (
                SELECT date(created_at) as study_date
                FROM study_sessions
                GROUP BY date(created_at)
            ),
            streak_calc AS (
                SELECT 
                    study_date,
                    julianday(study_date) - julianday(lag(study_date, 1) over (order by study_date)) as days_diff
                FROM daily_sessions
            )
            SELECT COUNT(*) FROM (
                SELECT study_date FROM streak_calc
                WHERE days_diff = 1 OR days_diff IS NULL
                ORDER BY study_date DESC
            )
        ''')).scalar()

        return StudyStatsResponse(
            total_vocabulary=total_vocabulary,
            total_words_studied=total_words,
            mastered_words=mastered_words,
            success_rate=success_rate,
            total_sessions=total_sessions,
            active_groups=active_groups,
            current_streak=current_streak
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
