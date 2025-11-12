from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.deps import Base

class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    educationality = Column(Float, default=0.0)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    distance_miles = Column(Float, nullable=True)
    website_url = Column(String, nullable=True)
    booking_url = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    parking_notes = Column(String, nullable=True)
    disclosure_needed = Column(Boolean, default=False)
    image_allowed = Column(Boolean, default=True)
    availability_status = Column(String, default="unknown")
    availability_source = Column(String, nullable=True)
    amenities = Column(JSON, default=dict)
    score_total = Column(Float, default=0.0)
    score_components = Column(JSON, default=dict)
    reason_text = Column(String, nullable=True)

    rooms = relationship("Room", back_populates="venue", cascade="all, delete-orphan")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"))
    room_name = Column(String, nullable=True)
    capacity_classroom = Column(Integer, nullable=True)
    capacity_theater = Column(Integer, nullable=True)
    fees_hour = Column(Float, nullable=True)
    fees_day = Column(Float, nullable=True)
    deposit = Column(Float, nullable=True)
    rental_policy_url = Column(String, nullable=True)

    venue = relationship("Venue", back_populates="rooms")
