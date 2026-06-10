from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID
import os
from dotenv import load_dotenv

from models import (
    UserCreate, UserResponse,
    CarCreate, CarResponse,
    NoteCreate, NoteResponse,
    MaintenanceEventCreate, MaintenanceEventResponse,
    AIResponseModel, HealthCheckResponse
)
from database import db
from claude_service import get_claude_service

load_dotenv()

# ─── Startup and Shutdown ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic for the app.
    Connects to database on startup, closes on shutdown.
    """
    print("🚀 Starting Car Assistant API...")
    db.connect()
    yield
    print("🛑 Shutting down...")
    db.disconnect()


# ─── Initialize FastAPI App ──────────────────────────────────

app = FastAPI(
    title="Car Assistant API",
    description="AI-powered car maintenance and documentation assistant",
    version="0.1.0",
    lifespan=lifespan
)


# ─── Health Check Endpoint ───────────────────────────────────

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check if API and database are healthy"""
    try:
        # Quick database query to verify connection
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT 1")
        
        return HealthCheckResponse(
            status="healthy",
            database="connected",
            message="API and database are running"
        )
    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            database="disconnected",
            message=f"Database error: {str(e)}"
        )


# ─── User Endpoints ──────────────────────────────────────────

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Register a new user"""
    try:
        query = """
            INSERT INTO users (email, full_name)
            VALUES (%s, %s)
            RETURNING id, email, full_name, created_at
        """
        result = db.execute_insert(query, (user.email, user.full_name))
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID):
    """Get a specific user"""
    try:
        query = "SELECT id, email, full_name, created_at FROM users WHERE id = %s"
        result = db.execute_query(query, (str(user_id),))
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result[0]
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Car Endpoints ───────────────────────────────────────────

@app.post("/cars", response_model=CarResponse)
async def create_car(user_id: UUID, car: CarCreate):
    """Create a new car for a user"""
    try:
        query = """
            INSERT INTO cars (user_id, make, model, year, vin, fuel_type, engine_size)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, make, model, year, vin, fuel_type, engine_size, created_at
        """
        result = db.execute_insert(
            query,
            (str(user_id), car.make, car.model, car.year, car.vin, car.fuel_type, car.engine_size)
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create car")
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/cars/{car_id}", response_model=CarResponse)
async def get_car(car_id: UUID):
    """Get a specific car"""
    try:
        query = """
            SELECT id, user_id, make, model, year, vin, fuel_type, engine_size, created_at
            FROM cars WHERE id = %s
        """
        result = db.execute_query(query, (str(car_id),))
        
        if not result:
            raise HTTPException(status_code=404, detail="Car not found")
        
        return result[0]
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}/cars")
async def list_user_cars(user_id: UUID):
    """List all cars for a user"""
    try:
        query = """
            SELECT id, user_id, make, model, year, vin, fuel_type, engine_size, created_at
            FROM cars WHERE user_id = %s
            ORDER BY created_at DESC
        """
        results = db.execute_query(query, (str(user_id),))
        return results
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Note Endpoints ──────────────────────────────────────────

@app.post("/notes", response_model=NoteResponse)
async def create_note(car_id: UUID, note: NoteCreate):
    """Create a new note (voice or manual)"""
    try:
        query = """
            INSERT INTO notes (car_id, note_type, category, content, recorded_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, car_id, note_type, category, content, recorded_at, created_at
        """
        result = db.execute_insert(
            query,
            (str(car_id), note.note_type, note.category, note.content, note.recorded_at)
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create note")
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/cars/{car_id}/notes")
async def list_car_notes(car_id: UUID):
    """List all notes for a car"""
    try:
        query = """
            SELECT id, car_id, note_type, category, content, recorded_at, created_at
            FROM notes WHERE car_id = %s
            ORDER BY recorded_at DESC
        """
        results = db.execute_query(query, (str(car_id),))
        return results
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Maintenance Event Endpoints ──────────────────────────────

@app.post("/maintenance", response_model=MaintenanceEventResponse)
async def create_maintenance_event(car_id: UUID, event: MaintenanceEventCreate):
    """Create a new maintenance event"""
    try:
        query = """
            INSERT INTO maintenance_events 
            (car_id, event_type, description, scheduled_at, completed_at, mileage_at_event, cost, mechanic_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, car_id, event_type, description, scheduled_at, completed_at, mileage_at_event, cost, mechanic_name, created_at
        """
        result = db.execute_insert(
            query,
            (str(car_id), event.event_type, event.description, event.scheduled_at, 
             event.completed_at, event.mileage_at_event, event.cost, event.mechanic_name)
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create maintenance event")
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/cars/{car_id}/maintenance")
async def list_car_maintenance(car_id: UUID):
    """List all maintenance events for a car"""
    try:
        query = """
            SELECT id, car_id, event_type, description, scheduled_at, completed_at, mileage_at_event, cost, mechanic_name, created_at
            FROM maintenance_events WHERE car_id = %s
            ORDER BY scheduled_at DESC NULLS LAST
        """
        results = db.execute_query(query, (str(car_id),))
        return results
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── AI Chat Endpoint ────────────────────────────────────────

@app.post("/chat", response_model=AIResponseModel)
async def chat_with_ai(car_id: UUID, message: str):
    """
    Chat with Claude AI about the car.
    Claude can see past notes and car documentation.
    """
    try:
        # Get car info
        car_query = "SELECT make, model, year FROM cars WHERE id = %s"
        car_result = db.execute_query(car_query, (str(car_id),))
        
        if not car_result:
            raise HTTPException(status_code=404, detail="Car not found")
        
        car = car_result[0]
        car_context = f"{car['make']} {car['model']} {car['year']}"
        
        # Get recent notes for context (simplified — full version uses pgvector search)
        notes_query = """
            SELECT content FROM notes WHERE car_id = %s
            ORDER BY recorded_at DESC LIMIT 5
        """
        notes_results = db.execute_query(notes_query, (str(car_id),))
        past_notes = [n['content'] for n in notes_results]
        
        # Get Claude service and chat
        claude_service = get_claude_service()
        ai_response = claude_service.chat(
            user_message=message,
            car_context=car_context,
            past_notes=past_notes
        )
        
        return AIResponseModel(
            message=ai_response,
            related_notes=past_notes[:3] if past_notes else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Root Endpoint ───────────────────────────────────────────

@app.get("/")
async def root():
    """API welcome message"""
    return {
        "name": "Car Assistant API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


# ─── Error Handler ───────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch all errors and return clean responses"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)