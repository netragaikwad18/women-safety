import os
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, EmergencyAlert, AlertAcknowledgement, EmergencyContact, CommunityHelper
from backend.app.schemas import AlertCreate, AlertOut, AlertAcknowledgementCreate, AlertAcknowledgementOut
from backend.app.auth import get_current_user
from backend.app.services.notification_service import notification_service
from backend.app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/sos", tags=["Emergency SOS System"])

UPLOAD_DIR = "backend/app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/trigger", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
async def trigger_sos(alert_in: AlertCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Create emergency alert record
    alert = EmergencyAlert(
        user_id=current_user.id,
        trigger_type=alert_in.trigger_type,
        alert_mode=alert_in.alert_mode,
        status="active",
        latitude=alert_in.latitude,
        longitude=alert_in.longitude,
        location_address=alert_in.location_address or "Location verified via GPS",
        audio_recording_url=alert_in.audio_recording_url,
        battery_level_at_alert=alert_in.battery_level or current_user.battery_level,
        network_status_at_alert=alert_in.network_status or current_user.network_status,
        notes=alert_in.notes
    )
    db.add(alert)

    # Update user's last known coordinates
    current_user.last_latitude = alert_in.latitude
    current_user.last_longitude = alert_in.longitude
    current_user.last_location_time = datetime.utcnow()
    db.commit()
    db.refresh(alert)

    # 2. Query emergency contacts to dispatch alerts
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).all()
    phone_numbers = [c.phone_number for c in contacts if c.phone_number]

    # 3. Trigger emergency notifications (SMS and push)
    sms_response = notification_service.send_emergency_sms(
        phone_numbers=phone_numbers,
        user_name=current_user.full_name,
        latitude=alert.latitude,
        longitude=alert.longitude,
        address=alert.location_address,
        alert_mode=alert.alert_mode
    )

    # 4. Notify live WebSocket listeners (e.g. responders, community helpers, admin monitoring)
    payload = {
        "event": "NEW_SOS_ALERT",
        "alert_id": alert.id,
        "user_id": current_user.id,
        "user_name": current_user.full_name,
        "user_phone": current_user.phone,
        "latitude": alert.latitude,
        "longitude": alert.longitude,
        "alert_mode": alert.alert_mode,
        "trigger_type": alert.trigger_type,
        "battery_level": alert.battery_level_at_alert,
        "created_at": alert.created_at.isoformat(),
        "notifications": sms_response
    }
    await ws_manager.broadcast(payload)

    # Map user fields for response schema
    alert.user_name = current_user.full_name
    alert.user_phone = current_user.phone
    return alert

@router.get("/active", response_model=List[AlertOut])
def get_active_alerts(db: Session = Depends(get_db)):
    alerts = db.query(EmergencyAlert).filter(EmergencyAlert.status.in_(["active", "acknowledged"])).order_by(EmergencyAlert.created_at.desc()).all()
    for a in alerts:
        a.user_name = a.user.full_name if a.user else "Unknown"
        a.user_phone = a.user.phone if a.user else "N/A"
    return alerts

@router.get("/history", response_model=List[AlertOut])
def get_alert_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "admin":
        alerts = db.query(EmergencyAlert).order_by(EmergencyAlert.created_at.desc()).all()
    else:
        alerts = db.query(EmergencyAlert).filter(EmergencyAlert.user_id == current_user.id).order_by(EmergencyAlert.created_at.desc()).all()

    for a in alerts:
        a.user_name = a.user.full_name if a.user else "Unknown"
        a.user_phone = a.user.phone if a.user else "N/A"
    return alerts

@router.get("/{alert_id}", response_model=AlertOut)
def get_alert_details(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency alert not found")
    alert.user_name = alert.user.full_name if alert.user else "Unknown"
    alert.user_phone = alert.user.phone if alert.user else "N/A"
    return alert

@router.post("/{alert_id}/acknowledge", response_model=AlertAcknowledgementOut)
async def acknowledge_alert(
    alert_id: int,
    ack_in: AlertAcknowledgementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    # Check role
    responder_role = "community_helper" if current_user.role == "helper" else ("admin" if current_user.role == "admin" else "contact")

    ack = AlertAcknowledgement(
        alert_id=alert.id,
        responder_id=current_user.id,
        responder_role=responder_role,
        responder_name=current_user.full_name,
        responder_phone=current_user.phone,
        eta_minutes=ack_in.eta_minutes or 10,
        message=ack_in.message or "Assistance dispatched. Help is coming."
    )
    db.add(ack)
    alert.status = "acknowledged"

    # If responder is helper, increment count
    helper = db.query(CommunityHelper).filter(CommunityHelper.user_id == current_user.id).first()
    if helper:
        helper.accepted_requests_count += 1

    db.commit()
    db.refresh(ack)

    # Realtime notification to victim and broadcast
    await ws_manager.send_personal_message({
        "event": "SOS_ACKNOWLEDGED",
        "alert_id": alert.id,
        "responder_name": ack.responder_name,
        "responder_phone": ack.responder_phone,
        "eta_minutes": ack.eta_minutes,
        "message": ack.message
    }, user_id=alert.user_id)

    await ws_manager.broadcast({
        "event": "SOS_STATUS_UPDATED",
        "alert_id": alert.id,
        "status": "acknowledged",
        "responder_name": ack.responder_name
    })

    return ack

@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    # Authorized if victim, helper, or admin
    if alert.user_id != current_user.id and current_user.role not in ["admin", "helper"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to resolve this alert")

    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    if notes:
        alert.notes = notes
    db.commit()

    await ws_manager.broadcast({
        "event": "SOS_RESOLVED",
        "alert_id": alert.id,
        "resolved_at": alert.resolved_at.isoformat()
    })
    return {"status": "success", "message": "Emergency alert marked as resolved"}

@router.put("/{alert_id}/cancel")
async def cancel_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accidental cancellation during or shortly after countdown"""
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel another user's alert")

    alert.status = "cancelled"
    alert.resolved_at = datetime.utcnow()
    alert.notes = "Cancelled by user (accidental trigger)"
    db.commit()

    await ws_manager.broadcast({
        "event": "SOS_CANCELLED",
        "alert_id": alert.id,
        "message": "User cancelled the emergency SOS alert."
    })
    return {"status": "success", "message": "Emergency alert cancelled"}

@router.post("/upload-audio")
async def upload_audio_recording(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Uploads emergency audio recording with user consent"""
    filename = f"emergency_audio_user_{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "success",
        "url": f"/static/uploads/{filename}",
        "filename": filename
    }
