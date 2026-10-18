
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
class EventCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    venue_id: int = Field(gt=0)
    performer_id: int = Field(gt=0)
    tickets: int = Field(ge=0)
    description: str = ""


class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    venue_id: int | None = Field(default=None, gt=0)
    performer_id: int | None = Field(default=None, gt=0)
    tickets: int | None = Field(default=None, ge=0)
    description: str | None = None


class EventOut(BaseModel):
    id: int
    venue_id: int
    performer_id: int
    name: str
    tickets: int
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VenueCreate(BaseModel):
    location: str = ""
    seatmap: str = ""


class VenueOut(BaseModel):
    id: int
    location: str
    seatmap: str
    event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PerformerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = ""


class PerformerOut(BaseModel):
    id: int
    name: str
    description: str
    event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    event_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=10)


class BookingOut(BaseModel):
    id: int
    event_id: int
    quantity: int
    total_minor: int
    currency: str
    status: str
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)
