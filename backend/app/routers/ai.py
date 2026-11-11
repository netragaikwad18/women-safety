from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import IncidentReport
from backend.app.schemas import RiskPredictionRequest, RiskPredictionResponse
from backend.app.services.risk_predictor import risk_predictor
from backend.app.routers.routes import EMERGENCY_SERVICES

router = APIRouter(prefix="/ai", tags=["AI Safety & Risk Prediction"])

@router.post("/predict-risk", response_model=RiskPredictionResponse)
def predict_risk(req: RiskPredictionRequest, db: Session = Depends(get_db)):
    # Calculate incidents within area
    incidents_count = db.query(IncidentReport).count()
    nearby_incidents = min(incidents_count, 3)

    result = risk_predictor.predict(
        hour_of_day=req.hour_of_day,
        speed_kmh=req.speed_kmh or 5.0,
        route_deviation_meters=req.route_deviation_meters or 0.0,
        nearby_incident_count=nearby_incidents,
        battery_level=req.battery_percentage or 85,
        is_isolated_area=req.isolated_area or False,
        lighting_score=4 if req.isolated_area else 8
    )

    # Attach nearby safe spots
    safe_spots = [
        {"name": s["name"], "type": s["type"], "phone": s["phone"]}
        for s in EMERGENCY_SERVICES[:3]
    ]

    return RiskPredictionResponse(
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        reasons=result["reasons"],
        recommendations=result["recommendations"],
        nearby_safe_spots=safe_spots,
        model_version=result["model_version"],
        dataset_disclaimer=result["dataset_disclaimer"]
    )
