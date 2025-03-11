from fastapi import FastAPI
from database import engine, Base
from routes import dashboard, groups, study_activities, study_sessions, words

app = FastAPI()

app.include_router(dashboard.router)
app.include_router(groups.router)
app.include_router(study_activities.router)
app.include_router(study_sessions.router)
app.include_router(words.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Japanese Learning API"}
