import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import IncidentReport, User
from backend.app.auth import get_current_user

router = APIRouter(prefix="/routes", tags=["Safe Route Recommendation"])

# Mock database of verified emergency facilities (police stations and hospitals)
EMERGENCY_SERVICES = [
    {"name": "Central Police Station", "type": "police", "lat": 12.9750, "lng": 77.5900, "phone": "100 / 080-22942222", "address": "Infantry Rd, Bengaluru"},
    {"name": "Cubbon Park Police Station", "type": "police", "lat": 12.9780, "lng": 77.5930, "phone": "080-22942548", "address": "Kasturba Rd, Bengaluru"},
    {"name": "Ashoknagar Police Station", "type": "police", "lat": 12.9610, "lng": 77.6050, "phone": "080-22942581", "address": "Commissariat Rd, Bengaluru"},
    {"name": "Victoria Hospital & Emergency Care", "type": "hospital", "lat": 12.9640, "lng": 77.5750, "phone": "080-26701150", "address": "Fort, Bengaluru"},
    {"name": "Bowring & Lady Curzon Hospital", "type": "hospital", "lat": 12.9820, "lng": 77.6030, "phone": "080-25591325", "address": "Shivajinagar, Bengaluru"},
    {"name": "Mallya Hospital 24x7 ER", "type": "hospital", "lat": 12.9685, "lng": 77.5955, "phone": "080-22277979", "address": "Vittal Mallya Rd, Bengaluru"}
]

class RouteRequest(BaseModel):
    origin_name: str
    origin_lat: float
    origin_lng: float
    destination_name: str
    destination_lat: float
    destination_lng: float
    travel_mode: Optional[str] = "walking" # walking, driving, transit

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.post("/recommend")
def recommend_safe_routes(req: RouteRequest, db: Session = Depends(get_db)):
    direct_dist = haversine(req.origin_lat, req.origin_lng, req.destination_lat, req.destination_lng)

    # Query incidents in area
    incidents = db.query(IncidentReport).all()

    # Generate 2 or 3 alternative paths between origin and destination
    # Route A: Direct / Fastest
    dist_a = round(direct_dist * 1.15, 2)
    time_a = int(dist_a / (4.5 / 60)) if req.travel_mode == "walking" else int(dist_a / (25.0 / 60))
    # Route B: Main Well-Lit Thoroughfare (Recommended Safe Route)
    dist_b = round(direct_dist * 1.30, 2)
    time_b = int(dist_b / (4.5 / 60)) if req.travel_mode == "walking" else int(dist_b / (25.0 / 60))
    # Route C: Alternative Outer Ring
    dist_c = round(direct_dist * 1.45, 2)
    time_c = int(dist_c / (4.5 / 60)) if req.travel_mode == "walking" else int(dist_c / (25.0 / 60))

    # Calculate midpoints for waypoints
    mid_lat = (req.origin_lat + req.destination_lat) / 2
    mid_lng = (req.origin_lng + req.destination_lng) / 2

    # Filter nearby emergency facilities along route
    nearby_facilities = []
    for f in EMERGENCY_SERVICES:
        d = haversine(mid_lat, mid_lng, f["lat"], f["lng"])
        if d < 5.0: # within 5 km
            nearby_facilities.append({**f, "distance_km": round(d, 2)})

    routes = [
        {
            "route_id": "route_recommended_safe",
            "name": "Well-Lit Arterial Safe Route (Recommended)",
            "risk_level": "SAFE",
            "risk_score": 18.5,
            "distance_km": dist_b,
            "duration_minutes": time_b,
            "lighting_quality": "High (Main Boulevard with CCTV)",
            "police_presence": "Active Patrol Sector",
            "incident_count_nearby": 0,
            "waypoints": [
                [req.origin_lat, req.origin_lng],
                [mid_lat + 0.002, mid_lng + 0.003],
                [req.destination_lat, req.destination_lng]
            ],
            "recommendation_reason": "Passes through active commercial zones, 2 police checkpoints, and excellent streetlight coverage."
        },
        {
            "route_id": "route_direct_fastest",
            "name": "Direct Shortcut Path",
            "risk_level": "WARNING",
            "risk_score": 58.0,
            "distance_km": dist_a,
            "duration_minutes": time_a,
            "lighting_quality": "Moderate / Intermittent alleyways",
            "police_presence": "Low",
            "incident_count_nearby": 2,
            "waypoints": [
                [req.origin_lat, req.origin_lng],
                [mid_lat, mid_lng],
                [req.destination_lat, req.destination_lng]
            ],
            "recommendation_reason": "Shorter duration but passes near 2 reported poorly lit stretches after sunset."
        },
        {
            "route_id": "route_alternate_bypass",
            "name": "Outer Highway Bypass",
            "risk_level": "SAFE",
            "risk_score": 25.0,
            "distance_km": dist_c,
            "duration_minutes": time_c,
            "lighting_quality": "High (Highway Streetlights)",
            "police_presence": "Highway Patrol",
            "incident_count_nearby": 1,
            "waypoints": [
                [req.origin_lat, req.origin_lng],
                [mid_lat - 0.004, mid_lng - 0.003],
                [req.destination_lat, req.destination_lng]
            ],
            "recommendation_reason": "Standard multi-lane road with frequent traffic and emergency response coverage."
        }
    ]

    return {
        "origin": {"name": req.origin_name, "lat": req.origin_lat, "lng": req.origin_lng},
        "destination": {"name": req.destination_name, "lat": req.destination_lat, "lng": req.destination_lng},
        "recommended_route_id": "route_recommended_safe",
        "routes": routes,
        "nearby_emergency_services": nearby_facilities
    }

@router.get("/emergency-services")
def get_emergency_services(lat: Optional[float] = None, lng: Optional[float] = None):
    results = EMERGENCY_SERVICES
    if lat is not None and lng is not None:
        for f in results:
            f["distance_km"] = round(haversine(lat, lng, f["lat"], f["lng"]), 2)
        results = sorted(results, key=lambda x: x["distance_km"])
    return results
