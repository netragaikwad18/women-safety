import os
import joblib
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

MODEL_PATH = "backend/app/ml/artifacts/risk_model.joblib"

class RiskPredictor:
    def __init__(self):
        self.model = None
        self.features = []
        self.classes = []
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            data = joblib.load(MODEL_PATH)
            self.model = data["model"]
            self.features = data["features"]
            self.classes = data["classes"]
        else:
            self.model = None

    def predict(
        self,
        hour_of_day: int = None,
        speed_kmh: float = 5.0,
        route_deviation_meters: float = 0.0,
        nearby_incident_count: int = 1,
        battery_level: int = 80,
        is_isolated_area: bool = False,
        lighting_score: int = 7
    ) -> Dict[str, Any]:
        if hour_of_day is None:
            hour_of_day = datetime.now().hour

        input_data = pd.DataFrame([{
            "hour_of_day": hour_of_day,
            "speed_kmh": speed_kmh,
            "route_deviation_meters": route_deviation_meters,
            "nearby_incident_count": nearby_incident_count,
            "battery_level": battery_level,
            "is_isolated_area": 1 if is_isolated_area else 0,
            "lighting_score": lighting_score
        }])

        reasons = []
        recommendations = []

        # Analyze factors
        if hour_of_day >= 22 or hour_of_day <= 5:
            reasons.append("Late night or early morning travel window (increased vulnerability).")
            recommendations.append("Share live tracking with trusted contacts or neighbourhood helpers.")

        if is_isolated_area or lighting_score <= 4:
            reasons.append("Poor illumination or isolated pedestrian stretch.")
            recommendations.append("Stay on well-lit main boulevards or take verified commercial routes.")

        if route_deviation_meters > 200:
            reasons.append(f"Substantial route deviation detected ({int(route_deviation_meters)}m off planned path).")
            recommendations.append("Confirm travel destination or verify route on live GPS map.")

        if nearby_incident_count >= 2:
            reasons.append(f"{nearby_incident_count} community incidents reported in this vicinity.")
            recommendations.append("Be alert; prepare one-tap SOS or voice emergency activation.")

        if battery_level < 20:
            reasons.append(f"Low device battery ({battery_level}% remaining).")
            recommendations.append("Enable battery saver and notify emergency contacts before power drains.")

        if self.model:
            predicted_label = self.model.predict(input_data)[0]
            proba = self.model.predict_proba(input_data)[0]
            class_probs = dict(zip(self.classes, proba))
            # Calculate calibrated continuous score 0 to 100
            score = (class_probs.get("HIGH RISK", 0.0) * 100) + (class_probs.get("WARNING", 0.0) * 50)
            score = round(min(100.0, max(5.0, score)), 1)
        else:
            # Fallback heuristic
            score = 20.0
            if hour_of_day >= 22 or hour_of_day <= 5: score += 30.0
            if is_isolated_area: score += 25.0
            if route_deviation_meters > 200: score += 15.0
            predicted_label = "HIGH RISK" if score >= 65 else ("WARNING" if score >= 35 else "SAFE")

        if not recommendations:
            recommendations.append("Standard safety precautions apply. Route is clear and well-populated.")

        return {
            "risk_level": predicted_label,
            "risk_score": score,
            "reasons": reasons if reasons else ["Well-lit area during active daytime transit."],
            "recommendations": recommendations,
            "model_version": "RandomForest-v1.0 (Scikit-Learn)",
            "dataset_disclaimer": "AI model trained on synthetic data for safety pattern evaluation."
        }

risk_predictor = RiskPredictor()
