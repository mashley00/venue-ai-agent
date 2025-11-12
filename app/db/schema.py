from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class SearchInput(BaseModel):
    cities: List[str] = Field(default_factory=list)
    zips: List[str] = Field(default_factory=list)
    radius_miles: float = 6.0
    window_start: str
    window_end: str
    attendees: int = 30
    preferred_slots: List[str] = Field(default_factory=lambda: ["11:00","11:30","18:00","18:30"])

class VenueOut(BaseModel):
    id: Optional[int] = None
    name: str
    category: Optional[str] = None
    educationality: float = 0.0
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    distance_miles: Optional[float] = None
    website_url: Optional[str] = None
    booking_url: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    parking_notes: Optional[str] = None
    disclosure_needed: Optional[bool] = None
    image_allowed: Optional[bool] = None
    availability_status: Optional[str] = None
    availability_source: Optional[str] = None
    amenities: Dict[str, bool] = {}
    score_total: Optional[float] = None
    reason_text: Optional[str] = None

class RankResponse(BaseModel):
    results: List[VenueOut]
    export_csv: str
    export_xlsx: str
