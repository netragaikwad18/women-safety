from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(25), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user") # 'user', 'helper', 'admin'
    is_verified_helper = Column(Boolean, default=False)
    address = Column(String(255), nullable=True)
    emergency_notes = Column(Text, nullable=True)
    battery_level = Column(Integer, default=100)
    network_status = Column(String(50), default="Online")
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    last_location_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contacts = relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("EmergencyAlert", back_populates="user", cascade="all, delete-orphan")
    location_history = relationship("LocationHistory", back_populates="user", cascade="all, delete-orphan")
    safe_zones = relationship("SafeZone", back_populates="user", cascade="all, delete-orphan")
    journeys = relationship("Journey", back_populates="user", cascade="all, delete-orphan")
    checkins = relationship("SafetyCheckIn", back_populates="user", cascade="all, delete-orphan")
    helper_profile = relationship("CommunityHelper", back_populates="user", uselist=False, cascade="all, delete-orphan")

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_name = Column(String(120), nullable=False)
    relationship_type = Column(String(50), nullable=False) # Family, Friend, Neighbour, Guardian
    phone_number = Column(String(25), nullable=False)
    email = Column(String(150), nullable=True)
    is_priority = Column(Boolean, default=True)
    invitation_status = Column(String(20), default="accepted") # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="contacts")

class CommunityHelper(Base):
    __tablename__ = "community_helpers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    neighbourhood = Column(String(150), nullable=False)
    city = Column(String(100), nullable=False)
    police_station_jurisdiction = Column(String(150), nullable=True)
    verification_document = Column(String(255), nullable=True)
    verification_status = Column(String(20), default="pending") # pending, verified, rejected
    is_available = Column(Boolean, default=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    accepted_requests_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="helper_profile")

class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trigger_type = Column(String(30), default="button") # button, shake, voice, route_deviation, timer_checkin
    alert_mode = Column(String(20), default="normal") # normal, silent
    status = Column(String(20), default="active") # active, acknowledged, resolved, cancelled
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_address = Column(String(255), nullable=True)
    audio_recording_url = Column(String(255), nullable=True)
    battery_level_at_alert = Column(Integer, default=100)
    network_status_at_alert = Column(String(50), default="Online")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="alerts")
    acknowledgements = relationship("AlertAcknowledgement", back_populates="alert", cascade="all, delete-orphan")

class AlertAcknowledgement(Base):
    __tablename__ = "alert_acknowledgements"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("emergency_alerts.id", ondelete="CASCADE"), nullable=False)
    responder_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    responder_role = Column(String(50), nullable=False) # contact, community_helper, admin
    responder_name = Column(String(120), nullable=False)
    responder_phone = Column(String(25), nullable=False)
    eta_minutes = Column(Integer, default=10)
    message = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime, default=datetime.utcnow)

    alert = relationship("EmergencyAlert", back_populates="acknowledgements")

class LocationHistory(Base):
    __tablename__ = "location_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, default=0.0)
    accuracy = Column(Float, default=10.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="location_history")

class SafeZone(Base):
    __tablename__ = "safe_zones"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    zone_name = Column(String(100), nullable=False) # Home, College, Workplace
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Integer, default=300)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="safe_zones")

class Journey(Base):
    __tablename__ = "journeys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    origin_name = Column(String(200), nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)
    destination_name = Column(String(200), nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)
    status = Column(String(30), default="in_progress") # in_progress, completed, deviated, cancelled
    risk_level = Column(String(20), default="SAFE")
    expected_arrival_time = Column(DateTime, nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="journeys")

class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    incident_type = Column(String(100), nullable=False) # Harassment, Poor Lighting, Isolated Area, Suspicious Activity
    description = Column(Text, nullable=False)
    risk_level = Column(String(20), default="WARNING") # SAFE, WARNING, HIGH RISK
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    reported_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=True)

class SafetyCheckIn(Base):
    __tablename__ = "safety_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(30), default="pending") # pending, completed, missed_alert_triggered
    checkin_deadline = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="checkins")
