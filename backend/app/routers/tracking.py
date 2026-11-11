from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, LocationHistory, SafeZone, Journey, SafetyCheckIn
from backend.app.schemas import (
    LocationUpdate, SafeZoneCreate, SafeZoneOut,
    JourneyCreate, JourneyOut
)
from backend.app.auth import get_current_user
from backend.app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/tracking", tags=["GPS & Live Tracking"])

@router.post("/location")
async def update_location(
    loc_in: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Record in history
    history_entry = LocationHistory(
        user_id=current_user.id,
        latitude=loc_in.latitude,
        longitude=loc_in.longitude,
        speed=loc_in.speed or 0.0,
        accuracy=loc_in.accuracy or 10.0,
        timestamp=datetime.utcnow()
    )
    db.add(history_entry)

    # Update User model state
    current_user.last_latitude = loc_in.latitude
    current_user.last_longitude = loc_in.longitude
    current_user.last_location_time = datetime.utcnow()
    if loc_in.battery_level is not None:
        current_user.battery_level = loc_in.battery_level
    if loc_in.network_status is not None:
        current_user.network_status = loc_in.network_status

    db.commit()

    # Broadcast location update to active WebSocket listeners
    await ws_manager.broadcast({
        "event": "USER_LOCATION_UPDATED",
        "user_id": current_user.id,
        "user_name": current_user.full_name,
        "latitude": loc_in.latitude,
        "longitude": loc_in.longitude,
        "speed": loc_in.speed,
        "battery_level": current_user.battery_level,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "status": "success",
        "latitude": current_user.last_latitude,
        "longitude": current_user.last_longitude,
        "battery_level": current_user.battery_level,
        "network_status": current_user.network_status
    }

@router.get("/last-known/{user_id}")
def get_last_known_location(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "user_id": user.id,
        "user_name": user.full_name,
        "phone": user.phone,
        "latitude": user.last_latitude,
        "longitude": user.last_longitude,
        "last_location_time": user.last_location_time,
        "battery_level": user.battery_level,
        "network_status": user.network_status
    }

@router.get("/history")
def get_location_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entries = db.query(LocationHistory).filter(
        LocationHistory.user_id == current_user.id
    ).order_by(LocationHistory.timestamp.desc()).limit(limit).all()
    return entries

# --- Safe Zones (Geofencing) ---
@router.post("/safe-zones", response_model=SafeZoneOut, status_code=status.HTTP_201_CREATED)
def create_safe_zone(zone_in: SafeZoneCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    zone = SafeZone(
        user_id=current_user.id,
        zone_name=zone_in.zone_name,
        latitude=zone_in.latitude,
        longitude=zone_in.longitude,
        radius_meters=zone_in.radius_meters or 300
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone

@router.get("/safe-zones", response_model=List[SafeZoneOut])
def get_safe_zones(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SafeZone).filter(SafeZone.user_id == current_user.id).all()

@router.delete("/safe-zones/{zone_id}")
def delete_safe_zone(zone_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    zone = db.query(SafeZone).filter(SafeZone.id == zone_id, SafeZone.user_id == current_user.id).first()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Safe zone not found")
    db.delete(zone)
    db.commit()
    return {"status": "success", "message": "Safe zone removed"}

# --- Journeys ---
@router.post("/journey/start", response_model=JourneyOut, status_code=status.HTTP_201_CREATED)
def start_journey(journey_in: JourneyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    eta = datetime.utcnow() + timedelta(minutes=journey_in.expected_duration_minutes or 30)
    journey = Journey(
        user_id=current_user.id,
        origin_name=journey_in.origin_name,
        origin_lat=journey_in.origin_lat,
        origin_lng=journey_in.origin_lng,
        destination_name=journey_in.destination_name,
        destination_lat=journey_in.destination_lat,
        destination_lng=journey_in.destination_lng,
        status="in_progress",
        expected_arrival_time=eta
    )
    db.add(journey)
    db.commit()
    db.refresh(journey)
    return journey

@router.put("/journey/{journey_id}/status")
def update_journey_status(
    journey_id: int,
    status_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    journey = db.query(Journey).filter(Journey.id == journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
    if status_str not in ["in_progress", "completed", "deviated", "cancelled"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    journey.status = status_str
    if status_str in ["completed", "cancelled"]:
        journey.end_time = datetime.utcnow()
    db.commit()
    return {"status": "success", "journey_status": journey.status}

# --- Safety Check-Ins ---
@router.post("/check-in/schedule")
def schedule_safety_checkin(
    duration_minutes: int = 15,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deadline = datetime.utcnow() + timedelta(minutes=duration_minutes)
    checkin = SafetyCheckIn(
        user_id=current_user.id,
        duration_minutes=duration_minutes,
        status="pending",
        checkin_deadline=deadline
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return {
        "status": "success",
        "checkin_id": checkin.id,
        "deadline": checkin.checkin_deadline.isoformat(),
        "duration_minutes": duration_minutes,
        "message": f"Safety check-in active for next {duration_minutes} minutes"
    }

@router.post("/check-in/{checkin_id}/confirm")
def confirm_safety_checkin(
    checkin_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    checkin = db.query(SafetyCheckIn).filter(
        SafetyCheckIn.id == checkin_id,
        SafetyCheckIn.user_id == current_user.id
    ).first()
    if not checkin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in record not found")
    checkin.status = "completed"
    db.commit()
    return {"status": "success", "message": "Safety check-in confirmed safe"}
