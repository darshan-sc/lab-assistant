from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from app.db import get_db
from app.core.config import settings
from app.api.routes.projects import router as projects_router
from app.api.routes.papers import router as papers_router
from app.api.routes.notes import router as notes_router
from app.api.routes.experiments import router as experiments_router

app = FastAPI(title="ResearchNexus API")

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(projects_router)
app.include_router(papers_router)
app.include_router(notes_router)
app.include_router(experiments_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to ResearchNexus API"}

@app.get("/db-ping")
def db_ping(db: Session = Depends(get_db)):
    db.execute(text("select 1"))
    return {"db": "ok"}