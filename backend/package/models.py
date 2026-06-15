from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

# ─── User Models ──────────────────────────────────────────────

class UserCreate(BaseModel):
    """User registration request"""
    email: str
    full_name: str

class UserResponse(BaseModel):
    """User in API responses"""
    id: UUID
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Car Models ───────────────────────────────────────────────

class CarCreate(BaseModel):
    """Create a new car"""
    make: str
    model: str
    year: int
    vin: Optional[str] = None
    fuel_type: Optional[str] = None
    engine_size: Optional[str] = None

class CarResponse(BaseModel):
    """Car in API responses"""
    id: UUID
    user_id: UUID
    make: str
    model: str
    year: int
    vin: Optional[str] = None
    fuel_type: Optional[str] = None
    engine_size: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Note Models ──────────────────────────────────────────────
# Unified model for both voice transcripts and manual notes

class NoteCreate(BaseModel):
    """Create a new note (voice or manual)"""
    note_type: str  # 'voice' or 'manual'
    category: Optional[str] = 'other'
    content: str
    recorded_at: datetime

class NoteResponse(BaseModel):
    """Note in API responses"""
    id: UUID
    car_id: UUID
    note_type: str
    category: str
    content: str
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Maintenance Event Models ─────────────────────────────────

class MaintenanceEventCreate(BaseModel):
    """Create a new maintenance event"""
    event_type: str  # oil_change, inspection, repair, etc
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    mileage_at_event: Optional[int] = None
    cost: Optional[float] = None
    mechanic_name: Optional[str] = None

class MaintenanceEventResponse(BaseModel):
    """Maintenance event in API responses"""
    id: UUID
    car_id: UUID
    event_type: str
    description: Optional[str]
    scheduled_at: Optional[datetime]
    completed_at: Optional[datetime]
    mileage_at_event: Optional[int]
    cost: Optional[float]
    mechanic_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Car Document Models ──────────────────────────────────────
# For storing car manual sections with embeddings

class CarDocumentCreate(BaseModel):
    """Create a new car document (manual section)"""
    section_title: Optional[str] = None
    content: str
    source_url: Optional[str] = None

class CarDocumentResponse(BaseModel):
    """Car document in API responses"""
    id: UUID
    car_id: UUID
    section_title: Optional[str]
    content: str
    source_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── API Response Models ───────────────────────────────────────

class AIResponseModel(BaseModel):
    """Response from Claude AI about a note or question"""
    message: str
    related_notes: Optional[list[str]] = None
    related_documents: Optional[list[str]] = None

class HealthCheckResponse(BaseModel):
    """Health check endpoint response"""
    status: str
    database: str
    message: str