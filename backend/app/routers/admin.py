from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models import User, EmergencyAlert, AlertAcknowledgement, CommunityHelper, IncidentReport
from backend.app.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Dashboard & Analytics"])

@router.get("/metrics")
def get_system_metrics(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).filter(User.role == "user").count()
    total_helpers = db.query(CommunityHelper).count()
    verified_helpers = db.query(CommunityHelper).filter(CommunityHelper.verification_status == "verified").count()
    pending_helpers = db.query(CommunityHelper).filter(CommunityHelper.verification_status == "pending").count()

    total_alerts = db.query(EmergencyAlert).count()
    active_alerts = db.query(EmergencyAlert).filter(EmergencyAlert.status.in_(["active", "acknowledged"])).count()
    resolved_alerts = db.query(EmergencyAlert).filter(EmergencyAlert.status == "resolved").count()
    cancelled_alerts = db.query(EmergencyAlert).filter(EmergencyAlert.status == "cancelled").count()

    total_incidents = db.query(IncidentReport).count()

    # Trigger distribution
    trigger_counts = {}
    triggers = db.query(EmergencyAlert.trigger_type, func.count(EmergencyAlert.id)).group_by(EmergencyAlert.trigger_type).all()
    for trig, cnt in triggers:
        trigger_counts[trig] = cnt

    return {
        "users": {
            "total_users": total_users,
            "total_helpers": total_helpers,
            "verified_helpers": verified_helpers,
            "pending_helpers": pending_helpers
        },
        "emergencies": {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": resolved_alerts,
            "cancelled_alerts": cancelled_alerts,
            "trigger_distribution": trigger_counts
        },
        "incidents": {
            "total_reports": total_incidents
        }
    }

@router.get("/users")
def list_all_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    results = []
    for u in users:
        results.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "is_verified_helper": u.is_verified_helper,
            "battery_level": u.battery_level,
            "network_status": u.network_status,
            "created_at": u.created_at.isoformat()
        })
    return results

@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    new_role: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if new_role not in ["user", "helper", "admin"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = new_role
    db.commit()
    return {"status": "success", "message": f"User role updated to {new_role}"}
