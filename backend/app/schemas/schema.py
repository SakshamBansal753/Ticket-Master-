from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


# -------------------------
# Event Schemas
# -------------------------

class EventCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    venue_id: int = Field(gt=0)
    performer_id: int = Field(gt=0)
    tickets: int = Field(ge=0)
    description: str = ""
    price_minor: int = Field(ge=0, default=0)


class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    venue_id: int | None = Field(default=None, gt=0)
    performer_id: int | None = Field(default=None, gt=0)
    tickets: int | None = Field(default=None, ge=0)
    description: str | None = None
    price_minor: int | None = Field(default=None, ge=0)


class EventOut(BaseModel):
    id: int
    venue_id: int
    performer_id: int
    name: str
    tickets: int
    description: str
    created_at: datetime
    price_minor: int

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Venue Schemas
# -------------------------

class VenueCreate(BaseModel):
    location: str = Field(default="", max_length=250)
    seatmap: str = ""


class VenueOut(BaseModel):
    id: int
    location: str
    seatmap: str
    event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Performer Schemas
# -------------------------

class PerformerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = ""
class UserSignin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)

class PerformerOut(BaseModel):
    id: int
    name: str
    description: str
    event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Booking Schemas
# -------------------------

class BookingCreate(BaseModel):
    event_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=10)


class BookingOut(BaseModel):
    id: int
    event_id: int
    quantity: int
    total_minor: int
    currency: str
    status: Literal[
        "pending",
        "paid",
        "expired",
        "cancelled",
        "failed",
    ]
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Ticket Schemas
# -------------------------

class TicketOut(BaseModel):
    id: int
    booking_id: int
    user_id: int
    qr_code: str
    checked_in: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# User Schemas
# -------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    performer: bool = False
    name: str | None = Field(default=None, min_length=2, max_length=100)
    created_at: datetime | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str | None
    performer: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
class UserProfileOut(BaseModel):
    id: int
    email: EmailStr
    performer: bool
    created_at: datetime
    name: str | None

    model_config = ConfigDict(from_attributes=True)
class BookingConfirmation(BaseModel):
    message: str
    booking: BookingOut
class UTRSubmission(BaseModel):
    payment_reference_number: str = Field(min_length=12, max_length=22, pattern=r"^[A-Za-z0-9-]+$"),


       