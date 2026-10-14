from datetime import datetime,timedelta,timezone
from fastapi import FastAPI,Depends,HTTPException,Response
from sqlalchemy import select,func
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.config import Settings
from app.database import Base,engine,get_db
stripe.api_key = Settings.stripe_secret_key
from contextlib import asynccontextmanager

@asynccontextmanager
def lifespan(app:FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(title="Event Booking API", version="0.1.0", lifespan=lifespan)
@app.get("/health")
def health():
    return {"status":"ok"}
