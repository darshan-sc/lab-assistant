from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
from app.api.routes.papers import router as papers_router

app = FastAPI(title="Lab Assistant API")


app.include_router(papers_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Lab Assistant API"}

@app.get("/db-ping")
def db_ping(db: Session = Depends(get_db)):
    db.execute(text("select 1"))
    return {"db": "ok"}