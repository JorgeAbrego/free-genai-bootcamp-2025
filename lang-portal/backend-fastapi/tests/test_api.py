import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

client = TestClient(app)

### Tests for `/groups`
def test_get_groups():
    response = client.get("/groups")
    assert response.status_code == 200
    assert "groups" in response.json()
    assert "total_pages" in response.json()

def test_get_group_not_found():
    response = client.get("/groups/9999")
    assert response.status_code == 404

### Tests for `/study-sessions`
def test_create_study_session():
    payload = {"group_id": 1, "study_activity_id": 1}
    response = client.post("/study-sessions/", json=payload)
    assert response.status_code == 201
    assert "session_id" in response.json()

def test_create_study_session_missing_group():
    payload = {"study_activity_id": 1}
    response = client.post("/study-sessions/", json=payload)
    assert response.status_code == 422

def test_get_study_session_not_found():
    response = client.get("/study-sessions/9999") 
    assert response.status_code == 404

### Tests for `/words`
def test_get_words():
    response = client.get("/words")
    assert response.status_code == 200
    assert "items" in response.json()

def test_get_word_not_found():
    response = client.get("/words/9999")
    assert response.status_code == 404

### Tests for `/study-activities`
def test_get_study_activities():
    response = client.get("/study-activities/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_study_activity_not_found():
    response = client.get("/study-activities/9999")
    assert response.status_code == 404

### Tests for `/study-sessions/{id}/review`
def test_log_review():
    payload = {"word_id": 1, "correct": True}
    response = client.post("/study-sessions/1/review", json=payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Review logged successfully"}

def test_log_review_missing_fields():
    payload = {"word_id": 1} 
    response = client.post("/study-sessions/1/review", json=payload)
    assert response.status_code == 422

### Tests for `/groups/{id}/words/raw`
def test_get_group_words_raw():
    response = client.get("/groups/1/words/raw")
    assert response.status_code == 200
    assert "words" in response.json()

def test_get_group_words_raw_not_found():
    response = client.get("/groups/9999/words/raw")
    assert response.status_code == 404
