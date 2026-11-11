from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Auth & User ---
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    role: Optional[str] = "user"
    address: Optional[str] = None
    emergency_notes: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_notes: Optional[str] = None
    battery_level: Optional[int] = None
    network_status: Optional[str] = None

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    role: str
    is_verified_helper: bool
    address: Optional[str] = None
    emergency_notes: Optional[str] = None
    battery_level: int
    network_status: str
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    last_location_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

# --- Emergency Contact ---
class ContactCreate(BaseModel):
    contact_name: str
    relationship_type: str
    phone_number: str
    email: Optional[EmailStr] = None
    is_priority: Optional[bool] = True

class ContactOut(BaseModel):
    id: int
    user_id: int
    contact_name: str
    relationship_type: str
    phone_number: str
    email: Optional[str] = None
    is_priority: bool
    invitation_status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Community Helper ---
class HelperRegister(BaseModel):
    neighbourhood: str
    city: str
    police_station_jurisdiction: Optional[str] = None
    verification_document: Optional[str] = None

class HelperOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    phone: str
    neighbourhood: str
    city: str
    police_station_jurisdiction: Optional[str] = None
    verification_status: str
    is_available: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accepted_requests_count: int

    class Config:
        from_attributes = True

# --- Emergency Alert SOS ---
class AlertCreate(BaseModel):
    latitude: float
    longitude: float
    trigger_type: Optional[str] = "button" # button, shake, voice, route_deviation, timer_checkin
    alert_mode: Optional[str] = "normal" # normal, silent
    location_address: Optional[str] = None
    audio_recording_url: Optional[str] = None
    battery_level: Optional[int] = 100
    network_status: Optional[str] = "Online"
    notes: Optional[str] = None

class AlertAcknowledgementCreate(BaseModel):
    eta_minutes: Optional[int] = 10
    message: Optional[str] = "Help is on the way!"

class AlertAcknowledgementOut(BaseModel):
    id: int
    alert_id: int
    responder_id: int
    responder_role: str
    responder_name: str
    responder_phone: str
    eta_minutes: int
    message: Optional[str] = None
    acknowledged_at: datetime

    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    trigger_type: str
    alert_mode: str
    status: str
    latitude: float
    longitude: float
    location_address: Optional[str] = None
    audio_recording_url: Optional[str] = None
    battery_level_at_alert: int
    network_status_at_alert: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None
    acknowledgements: List[AlertAcknowledgementOut] = []

    class Config:
        from_attributes = True

# --- GPS Tracking & Journey ---
class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    speed: Optional[float] = 0.0
    accuracy: Optional[float] = 10.0
    battery_level: Optional[int] = None
    network_status: Optional[str] = None

class SafeZoneCreate(BaseModel):
    zone_name: str
    latitude: float
    longitude: float
    radius_meters: Optional[int] = 300

class SafeZoneOut(BaseModel):
    id: int
    user_id: int
    zone_name: str
    latitude: float
    longitude: float
    radius_meters: int
    created_at: datetime

    class Config:
        from_attributes = True

class JourneyCreate(BaseModel):
    origin_name: str
    origin_lat: float
    origin_lng: float
    destination_name: str
    destination_lat: float
    destination_lng: float
    expected_duration_minutes: Optional[int] = 30

class JourneyOut(BaseModel):
    id: int
    user_id: int
    origin_name: str
    origin_lat: float
    origin_lng: float
    destination_name: str
    destination_lat: float
    destination_lng: float
    status: str
    risk_level: str
    expected_arrival_time: Optional[datetime] = None
    start_time: datetime
    end_time: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Incident Report ---
class IncidentReportCreate(BaseModel):
    incident_type: str
    description: str
    risk_level: Optional[str] = "WARNING"
    latitude: float
    longitude: float

class IncidentReportOut(BaseModel):
    id: int
    reporter_id: Optional[int] = None
    incident_type: str
    description: str
    risk_level: str
    latitude: float
    longitude: float
    reported_at: datetime
    is_verified: bool

    class Config:
        from_attributes = True

# --- AI Prediction ---
class RiskPredictionRequest(BaseModel):
    latitude: float
    longitude: float
    hour_of_day: Optional[int] = None
    speed_kmh: Optional[float] = 5.0
    route_deviation_meters: Optional[float] = 0.0
    battery_percentage: Optional[int] = 85
    isolated_area: Optional[bool] = False

class RiskPredictionResponse(BaseModel):
    risk_level: str # SAFE, WARNING, HIGH RISK
    risk_score: float # 0.0 to 100.0
    reasons: List[str]
    recommendations: List[str]
    nearby_safe_spots: List[dict]
    model_version: str
    dataset_disclaimer: str

# --- Chatbot ---
class ChatMessage(BaseModel):
    message: str
    language: Optional[str] = "en" # 'en' or 'kn'

class ChatResponse(BaseModel):
    response: str
    language: str
    suggested_actions: List[str]
    emergency_numbers: dict
