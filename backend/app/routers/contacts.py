from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db
from backend.app.models import User, EmergencyContact
from backend.app.schemas import ContactCreate, ContactOut
from backend.app.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["Emergency Contacts & Network"])

@router.get("", response_model=List[ContactOut])
def get_user_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).all()

@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
def add_contact(contact_in: ContactCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = EmergencyContact(
        user_id=current_user.id,
        contact_name=contact_in.contact_name,
        relationship_type=contact_in.relationship_type,
        phone_number=contact_in.phone_number,
        email=contact_in.email,
        is_priority=contact_in.is_priority if contact_in.is_priority is not None else True,
        invitation_status="accepted" # default accepted in demo/prototype
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact

@router.delete("/{contact_id}", status_code=status.HTTP_200_OK)
def delete_contact(contact_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return {"status": "success", "message": "Emergency contact removed"}

@router.put("/{contact_id}/invitation-status")
def update_invitation_status(contact_id: int, status_str: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if status_str not in ["pending", "accepted", "rejected"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation status")
    contact.invitation_status = status_str
    db.commit()
    return {"status": "success", "invitation_status": contact.invitation_status}
