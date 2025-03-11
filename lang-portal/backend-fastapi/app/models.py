from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, func, JSON
from sqlalchemy.orm import relationship
from database import Base


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    kanji = Column(String, nullable=False)
    romaji = Column(String, nullable=False)
    english = Column(String, nullable=False)
    parts = Column(JSON, nullable=False)

    word_groups = relationship("WordGroup", back_populates="word")


class WordGroup(Base):
    __tablename__ = "word_groups"

    word_id = Column(Integer, ForeignKey("words.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)

    word = relationship("Word", back_populates="word_groups")
    group = relationship("Group", back_populates="word_groups")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    words_count = Column(Integer, default=0)
    
    word_groups = relationship("WordGroup", back_populates="group")
    

class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    study_activity_id = Column(Integer, ForeignKey("study_activities.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    group = relationship("Group")
    study_activity = relationship("StudyActivity")


class StudyActivity(Base):
    __tablename__ = "study_activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    preview_url = Column(String, nullable=True)
    
    
class WordReviewItem(Base):
    __tablename__ = "word_review_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    study_session_id = Column(Integer, ForeignKey("study_sessions.id"), nullable=False)
    correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=func.now())

    word = relationship("Word")
    study_session = relationship("StudySession")


class WordReview(Base):
    __tablename__ = "word_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime, default=func.now())

    word = relationship("Word")
    