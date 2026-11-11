from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, CommunityHelper
from backend.app.schemas import HelperRegister, HelperOut
from backend.app.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/community", tags=["Community Helpers & Neighbourhood Network"])

@router.post("/register-helper")
def register_as_helper(
    data: HelperRegister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(CommunityHelper).filter(CommunityHelper.user_id == current_user.id).first()
    if existing:
        existing.neighbourhood = data.neighbourhood
        existing.city = data.city
        existing.police_station_jurisdiction = data.police_station_jurisdiction
        existing.verification_document = data.verification_document or existing.verification_document
        existing.verification_status = "pending"
        db.commit()
        return {"status": "success", "message": "Helper application updated, awaiting verification"}

    helper = CommunityHelper(
        user_id=current_user.id,
        neighbourhood=data.neighbourhood,
        city=data.city,
        police_station_jurisdiction=data.police_station_jurisdiction,
        verification_document=data.verification_document or "community_id_verified",
        verification_status="pending",
        is_available=True
    )
    current_user.role = "helper"
    db.add(helper)
    db.commit()
    db.refresh(helper)
    return {"status": "success", "message": "Registered as emergency community helper (pending review)"}

@router.get("/helpers")
def list_community_helpers(
    neighbourhood: Optional[str] = None,
    verified_only: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(CommunityHelper, User).join(User, CommunityHelper.user_id == User.id)
    if verified_only:
        query = query.filter(CommunityHelper.verification_status == "verified")
    if neighbourhood:
        query = query.filter(CommunityHelper.neighbourhood.ilike(f"%{neighbourhood}%"))

    results = []
    for helper, user in query.all():
        results.append({
            "id": helper.id,
            "user_id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "neighbourhood": helper.neighbourhood,
            "city": helper.city,
            "police_station_jurisdiction": helper.police_station_jurisdiction,
            "verification_status": helper.verification_status,
            "is_available": helper.is_available,
            "latitude": user.last_latitude or 12.9716,
            "longitude": user.last_longitude or 77.5946,
            "accepted_requests_count": helper.accepted_requests_count
        })
    return results

@router.put("/helpers/{helper_id}/verify")
def verify_helper(
    helper_id: int,
    approve: bool = True,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    helper = db.query(CommunityHelper).filter(CommunityHelper.id == helper_id).first()
    if not helper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Helper not found")
    helper.verification_status = "verified" if approve else "rejected"
    user = db.query(User).filter(User.id == helper.user_id).first()
    if user:
        user.is_verified_helper = approve
    db.commit()
    return {"status": "success", "verification_status": helper.verification_status}

@router.put("/helpers/toggle-availability")
def toggle_helper_availability(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    helper = db.query(CommunityHelper).filter(CommunityHelper.user_id == current_user.id).first()
    if not helper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not registered as helper")
    helper.is_available = not helper.is_available
    db.commit()
    return {"status": "success", "is_available": helper.is_available}
