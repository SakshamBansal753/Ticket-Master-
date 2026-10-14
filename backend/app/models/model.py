
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("tickets >= 0", name="ck_events_tickets_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="RESTRICT"),
        index=True,
    )
    performer_id: Mapped[int] = mapped_column(
        ForeignKey("performers.id", ondelete="RESTRICT"),
        index=True,
    )

    name: Mapped[str] = mapped_column(String(200), index=True)
    tickets: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    venue: Mapped["Venue"] = relationship(back_populates="events")
    performer: Mapped["Performer"] = relationship(back_populates="events")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="event")



class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    location: Mapped[str] = mapped_column(String(250), default="")
    seatmap: Mapped[str] = mapped_column(Text, default="")

    events: Mapped[list["Event"]] = relationship(back_populates="venue")


class Performer(Base):
    __tablename__ = "performers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")

    events: Mapped[list["Event"]] = relationship(back_populates="performer")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_bookings_quantity_positive"),
        CheckConstraint(
            "total_minor >= 0",
            name="ck_bookings_total_nonnegative",
        ),
        CheckConstraint(
            "status IN ('pending', 'paid', 'expired', 'cancelled', 'failed')",
            name="ck_bookings_status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT"),
        index=True,
    )

    quantity: Mapped[int] = mapped_column(Integer)
    total_minor: Mapped[int] = mapped_column(Integer)

    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True,
    )

    checkout_session_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    event: Mapped["Event"] = relationship(back_populates="bookings")
