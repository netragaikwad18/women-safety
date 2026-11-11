from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import IncidentReport, User
from backend.app.schemas import IncidentReportCreate, IncidentReportOut
from backend.app.auth import get_current_user

router = APIRouter(prefix="/hotspots", tags=["Crime Hotspots & Community Incidents"])

# Preset seed incidents for interactive crime hotspot map
DEFAULT_HOTSPOTS = [
    {
        "incident_type": "Poor Lighting & Isolated Stretch",
        "description": "Streetlights non-functional past 8 PM; frequent complaints of harassment near old underpass.",
        "risk_level": "HIGH RISK",
        "latitude": 12.9690,
        "longitude": 77.5850,
        "is_verified": True
    },
    {
        "incident_type": "Suspicious Loitering",
        "description": "Groups loitering near vacant industrial plot, catcalling reported by pedestrians.",
        "risk_level": "WARNING",
        "latitude": 12.9815,
        "longitude": 77.6120,
        "is_verified": True
    },
    {
        "incident_type": "Unlit Alleyway Shortcut",
        "description": "Blind corner behind bus depot without street surveillance.",
        "risk_level": "WARNING",
        "latitude": 12.9550,
        "longitude": 77.5920,
        "is_verified": True
    },
    {
        "incident_type": "Commercial High-Safety Zone",
        "description": "Active shopping precinct with continuous police presence and 24/7 CCTV coverage.",
        "risk_level": "SAFE",
        "latitude": 12.9738,
        "longitude": 77.6080,
        "is_verified": True
    }
]

@router.get("", response_model=List[IncidentReportOut])
def list_incident_reports(db: Session = Depends(get_db)):
    # If empty, seed default demonstration records
    count = db.query(IncidentReport).count()
    if count == 0:
        for spot in DEFAULT_HOTSPOTS:
            db.add(IncidentReport(**spot))
        db.commit()

    return db.query(IncidentReport).order_by(IncidentReport.reported_at.desc()).all()

@router.post("", response_model=IncidentReportOut, status_code=status.HTTP_201_CREATED)
def report_incident(
    report_in: IncidentReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = IncidentReport(
        reporter_id=current_user.id,
        incident_type=report_in.incident_type,
        description=report_in.description,
        risk_level=report_in.risk_level or "WARNING",
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        is_verified=True
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.delete("/{incident_id}")
def delete_incident(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    if incident.reporter_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    db.delete(incident)
    db.commit()
    return {"status": "success", "message": "Incident removed"}
