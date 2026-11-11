# Smart Women Safety Alert System (NirbhayaSafe)

An intelligent, full-stack, and responsive women safety alert platform engineered with **FastAPI (Python)**, **MySQL / SQLite**, **Scikit-Learn Machine Learning**, **Bootstrap 5 / Leaflet Web UI**, and a cross-platform **Flutter / Dart Android application**.

---

## 1. System Architecture

```
                    +------------------------------------+
                    |  Web Browser Client (HTML/JS/Leaflet) |
                    +-----------------+------------------+
                                      |
                                      v  REST / WebSocket
+-----------------------------+       |
| Flutter Android Mobile App  +------->  FastAPI Backend (Port 8000)
| (Dart / Material Design 3)  |       |  - Auth & JWT
+-----------------------------+       |  - Emergency SOS Trigger & Hub
                                      |  - WebSocket Dispatch & Broadcast
                                      |  - Safe Route Finder
                                      |  - Crime Hotspot Geofence
                                      v  - Bilingual AI Safety Chatbot
               +---------------------------------------------------+
               |                                                   |
      +--------v------------+                             +--------v------------+
      |  MySQL 8 / SQLite   |                             |   Scikit-Learn AI   |
      |  Relational Storage |                             |   Risk Prediction   |
      +---------------------+                             +---------------------+
```

### Core Components:
1. **Shared FastAPI Backend & REST API (`backend/app`)**: Provides endpoints for authentication, emergency SOS, live GPS tracking, community network, safe routes, and notifications.
2. **AI/ML Risk Detection Pipeline (`backend/app/ml`)**: Random Forest classifier trained on spatio-temporal features to assess travel risk (`SAFE`, `WARNING`, `HIGH RISK`).
3. **Responsive Web Application (`backend/app/static`)**: Desktop and mobile-ready interface with interactive OpenStreetMap integration, 5-second countdown abort, safe route comparison, and admin dashboard.
4. **Flutter Android Application (`mobile_app/`)**: Native-ready mobile app sharing the same backend with shake triggers, silent SOS, and fake call simulator.

---

## 2. Database Schema Relationships

The schema is defined in `backend/schema.sql` (MySQL 8+ DDL) and mapped through SQLAlchemy in `backend/app/models/__init__.py`:

1. **`users`**: User identities, roles (`user`, `helper`, `admin`), last known GPS location, battery levels, and connectivity status.
2. **`emergency_contacts`**: Foreign key to `users(id)`. Family, friends, and guardians to alert during SOS.
3. **`community_helpers`**: Foreign key to `users(id)`. Verified local volunteers and emergency responders.
4. **`emergency_alerts`**: Foreign key to `users(id)`. Stores trigger mode (`normal`/`silent`), trigger origin (`button`, `shake`, `voice`), location coordinates, audio evidence, and status (`active`, `acknowledged`, `resolved`, `cancelled`).
5. **`alert_acknowledgements`**: Foreign keys to `emergency_alerts(id)` and `users(id)`. Responder ETAs, notes, and verification.
6. **`location_history`**: Continuous breadcrumb GPS trail for active tracking.
7. **`safe_zones`**: User geofenced safe perimeters (Home, College, Workplace).
8. **`journeys`**: Planned journeys with expected ETAs and deviation alerts.
9. **`incident_reports`**: Community-reported hazards and crime hotspots (poor lighting, harassment, unlit alleys).
10. **`safety_checkins`**: Scheduled check-in timers with automated SOS fail-safe.

---

## 3. Machine Learning Risk Detection

- **Synthetic Data Disclaimer**: Dataset generated in `backend/app/ml/synthetic_safety_data.csv` (3000 samples) explicitly labeled as synthetic for safety research and demo evaluation.
- **Features Analyzed**:
  - `hour_of_day` (Late night travel window increases risk)
  - `speed_kmh` (Prolonged halt or panic sprinting)
  - `route_deviation_meters` (Deviation away from planned path)
  - `nearby_incident_count` (Density of local safety hazards)
  - `battery_level` (Critical battery < 15%)
  - `is_isolated_area` & `lighting_score` (Streetlight illumination)
- **Outputs**:
  - `SAFE`, `WARNING`, `HIGH RISK` with transparent reason breakdown and actionable safety recommendations.

---

## 4. Bilingual AI Safety Chatbot (English & Kannada)

- Supports natural conversational safety advice in both **English** and **Kannada (ಕನ್ನಡ)**.
- Integrated directory of verified Indian emergency helplines:
  - **112**: All India National Emergency Helpline
  - **1091**: Women Helpline (Harassment & Abuse)
  - **181**: Women in Distress
  - **100**: Police
  - **108**: Emergency Ambulance Service
  - **1090**: Anti-Eve Teasing Squad (Bengaluru)

---

## 5. Quickstart & Installation Instructions

### Prerequisites
- Python 3.10+
- Flutter 3.x+ and Dart SDK
- (Optional) MySQL 8.0+ (Default configuration uses SQLite file `smart_safety.db` out-of-the-box)

### Step 1: Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 2: Train AI Risk Model & Generate Synthetic Dataset
```bash
PYTHONPATH=. python3 backend/app/ml/train_model.py
```

### Step 3: Run the FastAPI Server
```bash
PYTHONPATH=. uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- Open browser at `http://127.0.0.1:8000` to access the full responsive Web Application.
- Interactive Swagger API docs are available at `http://127.0.0.1:8000/docs`.

### Step 4: Run the Android Flutter Application
```bash
cd mobile_app
flutter pub get
flutter run
```

### Step 5: Run Automated Tests
```bash
# Run Backend Pytest Suite
PYTHONPATH=. pytest tests/test_api_integration.py -v

# Run Flutter Unit & Widget Tests
cd mobile_app && flutter test
```

---

## 6. External API Keys Configuration

For production deployment with live carrier SMS and push notifications, configure the environment variables:
- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`: For live carrier SMS dispatch.
- `FIREBASE_SERVER_KEY`: For real-time mobile push notifications.
*Note: In local and development mode, the system operates in explicit simulator mode, logging and returning full delivery tracking states.*
