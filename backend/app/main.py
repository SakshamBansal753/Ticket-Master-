from datetime import datetime,timedelta,timezone
from fastapi import FastAPI,Depends,HTTPException,Response
from sqlalchemy import select,func
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import Base,engine,get_db
from app.models.model import Event,Booking,Venue,Performer
import qrcode
from fastapi import FastAPI, Depends, HTTPException, Header, Request, Response
import stripe
from app.schemas.schema import EventCreate,EventUpdate,EventOut,BookingCreate,BookingOut,VenueOut,PerformerOut,VenueCreate,PerformerCreate
stripe.api_key = settings.stripe_secret_key
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app:FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(title="Event Booking API", version="0.1.0", lifespan=lifespan)
@app.get("/health")
def health():
    return {"status":"ok"}
@app.post("/events",response_model=EventOut,status_code=201)

def create_event(data: EventCreate, db: Session = Depends(get_db)):
    venue = db.get(Venue, data.venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    performer = db.get(Performer, data.performer_id)
    if performer is None:
        raise HTTPException(status_code=404, detail="Performer not found")

    event = Event(
        name=data.name,
        venue_id=data.venue_id,
        performer_id=data.performer_id,
        tickets=data.tickets,
        description=data.description,
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event
@app.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    return event

@app.post("/venue", response_model=VenueOut, status_code=201)
def create_venue(data:VenueCreate,db:Session=Depends(get_db)):
     venue=Venue(location=data.location,seatmap=data.seatmap)
     db.add(venue)
     db.commit()
     db.refresh(venue)
     return venue

@app.get("/venue/{venue_id}", response_model=VenueOut)
def get_venue(venue_id:int,db:Session=Depends(get_db)):
    venue=db.get(Venue,venue_id)
    if not venue:
        raise HTTPException(404,"Venue not found")
@app.get("/venue/{venue_id}")
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    venue = db.get(Venue, venue_id)

    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")

    event_count = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(Event.venue_id == venue_id)
    ) or 0

    return {
        "id": venue.id,
        "location": venue.location,
        "seatmap": venue.seatmap,
        "event_count": event_count,
    }
@app.post("/performer", response_model=PerformerOut, status_code=201)
def create_performer(data:PerformerCreate,db:Session=Depends(get_db)):
     performer=Performer(name=data.name,description=data.description)
     db.add(performer)
     db.commit()
     db.refresh(performer)
     return performer

@app.get("/performer/{performer_id}", response_model=PerformerOut)
def get_performer(performer_id:int,db:Session=Depends(get_db)):
    performer=db.get(Performer,performer_id)
    if not performer:
        raise HTTPException(404,"Performer not found")
    return performer

@app.get("/stats/events")
def get_event_stats(db: Session = Depends(get_db)):
    total_events = db.scalar(
        select(func.count()).select_from(Event)
    ) or 0

    return {
        "total_events": total_events
    }

@app.get("/venues")
def get_venues(db: Session = Depends(get_db)):
    statement = (
        select(
            Venue.id,
            Venue.location,
            Venue.seatmap,
            func.count(Event.id).label("event_count"),
        )
        .outerjoin(Event, Event.venue_id == Venue.id)
        .group_by(Venue.id, Venue.location, Venue.seatmap)
    )

    rows = db.execute(statement).all()

    return [
        {
            "id": row.id,
            "location": row.location,
            "seatmap": row.seatmap,
            "event_count": row.event_count,
        }
        for row in rows
    ]
