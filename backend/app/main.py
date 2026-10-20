from datetime import datetime,timedelta,timezone
from fastapi import FastAPI,Depends,HTTPException,Response
from sqlalchemy import select,func
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import Base,engine,get_db
from app.models.model import Event,Booking,Venue,Performer,User
import qrcode
from app.schemas.schema import UTRSubmission
from app.models.model import Booking, Ticket
from sqlalchemy.exc import IntegrityError
import secrets
import io
import qrcode
from urllib.parse import urlencode

from fastapi.responses import StreamingResponse
from pathlib import Path
from fastapi import Header, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from pwdlib import PasswordHash
from sqlalchemy import update
password_hash = PasswordHash.recommended()
from fastapi import FastAPI, Depends, HTTPException, Header, Request, Response
import stripe
from app.schemas.schema import EventCreate,EventUpdate,EventOut,BookingCreate,BookingOut,VenueOut,PerformerOut,VenueCreate,PerformerCreate,UserCreate,UserOut,UserSignin,UserProfileOut,BookingConfirmation

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
        price_minor=data.price_minor,
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
@app.post("/users/signup", response_model=UserOut, status_code=201)
def signup_user(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        password_hash=password_hash.hash(data.password),
        performer=data.performer,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create user",
        )

    return user


@app.post("/users/signin", response_model=UserOut)
def signin_user(
    data: UserSignin,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if user is None or not password_hash.verify(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return user
@app.get("/users/profile", response_model=UserProfileOut)
def get_user_profile(
    user_id: int = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user
@app.post(
    "/bookings",
    response_model=BookingConfirmation,
    status_code=201,
)
def create_booking(
    data: BookingCreate,
    user_id: int = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    event = db.get(Event, data.event_id)
    if event is None:
        raise HTTPException(404, "Event not found")

    now = datetime.now(timezone.utc)

    try:
        reservation = db.execute(
            update(Event)
            .where(
                Event.id == data.event_id,
                Event.tickets >= data.quantity,
            )
            .values(tickets=Event.tickets - data.quantity)
        )

        if reservation.rowcount != 1:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Not enough tickets available",
            )

        booking = Booking(
            event_id=data.event_id,
            user_id=user_id,
            quantity=data.quantity,
            total_minor=data.quantity * event.price_minor,
            currency="INR",
            status="pending",
            created_at=now,
            expires_at=now + timedelta(minutes=15),
        )

        db.add(booking)
        db.commit()
        db.refresh(booking)

        return {
            "message": (
                "Booking created successfully. "
                "Complete payment to confirm your tickets."
            ),
            "booking": booking,
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create booking",
        )
@app.get("/bookings/{booking_id}", response_model=BookingOut)
def get_booking(booking_id:int,user_id:int=Header(...,alias="X-User-ID"),db:Session=Depends(get_db)):
    booking=db.get(Booking,booking_id)
    if not booking:
        raise HTTPException(404,"Booking not found")
    if booking.user_id!=user_id:
        raise HTTPException(403,"You are not authorized to view this booking")
    return booking

@app.get("/bookings/{booking_id}/payment-qr")
def get_payment_qr(
    booking_id: int,
    user_id: int = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    booking = db.scalar(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == user_id,
        )
    )

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "pending":
        raise HTTPException(status_code=409, detail="Booking is not pending")

    now = datetime.now(timezone.utc)
    expiry = booking.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry <= now:
        raise HTTPException(status_code=409, detail="Booking has expired")

    if booking.currency.upper() != "INR":
        raise HTTPException(
            status_code=400,
            detail="UPI payments require INR",
        )

    amount = f"{booking.total_minor / 100:.2f}"

    upi_url = "upi://pay?" + urlencode({
        "pa": settings.upi_id,
        "pn": settings.upi_payee_name,
        "am": amount,
        "cu": "INR",
        "tn": f"Booking {booking.id}",
    })

    image = qrcode.make(upi_url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/bookings/{booking_id}/submit-utr", response_model=BookingOut)
def submit_payment_utr(
    booking_id: int,
    data: UTRSubmission,
    user_id: int = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    booking = db.scalar(
        select(Booking)
        .where(
            Booking.id == booking_id,
            Booking.user_id == user_id,
        )
        .with_for_update()
    )

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "pending":
        raise HTTPException(status_code=409, detail="Booking is not pending")

    now = datetime.now(timezone.utc)
    expiry = booking.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry <= now:
        raise HTTPException(status_code=409, detail="Booking has expired")

    if booking.payment_reference:
        raise HTTPException(
            status_code=409,
            detail="A payment reference has already been submitted",
        )

    booking.payment_reference = data.payment_reference.strip()
    booking.payment_submitted_at = now

    try:
        db.commit()
        db.refresh(booking)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This payment reference has already been submitted",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not submit payment reference",
        )

    return booking

@app.post("/admin/bookings/{booking_id}/confirm-payment")
def confirm_booking_payment(
    booking_id: int,
    admin_key: str = Header(..., alias="X-Admin-Key"),
    db: Session = Depends(get_db),
):
    # Check the admin secret before allowing payment confirmation.
    if not secrets.compare_digest(
        admin_key,
        settings.admin_payment_review_key,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid admin key",
        )

    try:
        # Lock the booking so concurrent confirmation requests
        # cannot issue tickets twice.
        booking = db.scalar(
            select(Booking)
            .where(Booking.id == booking_id)
            .with_for_update()
        )

        if booking is None:
            raise HTTPException(404, "Booking not found")

        # Make repeated confirmation requests safe.
        if booking.status == "paid":
            tickets = db.scalars(
                select(Ticket)
                .where(Ticket.booking_id == booking.id)
                .order_by(Ticket.id)
            ).all()

            if len(tickets) != booking.quantity:
                raise HTTPException(
                    status_code=500,
                    detail="Paid booking has an unexpected ticket count",
                )

            return {
                "message": "Booking already confirmed",
                "booking_id": booking.id,
                "status": booking.status,
                "tickets": [
                    {
                        "id": ticket.id,
                        "booking_id": ticket.booking_id,
                        "user_id": ticket.user_id,
                        "qr_code": ticket.qr_code,
                    }
                    for ticket in tickets
                ],
            }

        if booking.status != "pending":
            raise HTTPException(
                status_code=409,
                detail=f"Cannot confirm booking with status '{booking.status}'",
            )

        # A UTR must have been submitted first.
        if not booking.payment_reference:
            raise HTTPException(
                status_code=400,
                detail="No payment reference has been submitted",
            )

        # Reject expired bookings.
        now = datetime.now(timezone.utc)
        expiry = booking.expires_at

        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if expiry <= now:
            raise HTTPException(
                status_code=409,
                detail="Booking has expired",
            )

        # IMPORTANT:
        # Before calling this endpoint, manually verify that the
        # submitted UTR matches a successful payment in your bank
        # or merchant records, including the exact amount.

        # Create exactly one ticket per booked seat.
        new_tickets = []

        for _ in range(booking.quantity):
            ticket = Ticket(
                booking_id=booking.id,
                user_id=booking.user_id,
                qr_code=secrets.token_urlsafe(24),
                checked_in=False,
            )
            db.add(ticket)
            new_tickets.append(ticket)

        # Mark the booking paid in the same transaction as ticket creation.
        booking.status = "paid"
        booking.paid_at = now

        db.flush()

        result = {
            "message": "Payment verified and booking confirmed",
            "booking_id": booking.id,
            "status": "paid",
            "tickets": [
                {
                    "id": ticket.id,
                    "booking_id": booking.id,
                    "user_id": booking.user_id,
                    "qr_code": ticket.qr_code,
                }
                for ticket in new_tickets
            ],
        }

        db.commit()
        return result

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not confirm booking",
        )
