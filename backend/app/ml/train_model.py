"""
Machine Learning Model Training for Safety Risk Prediction
Trains a Random Forest Classifier and evaluates accuracy on test split.
"""

import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from backend.app.ml.generate_data import generate_synthetic_safety_data

MODEL_DIR = "backend/app/ml/artifacts"
MODEL_PATH = os.path.join(MODEL_DIR, "risk_model.joblib")
DATA_PATH = "backend/app/ml/synthetic_safety_data.csv"

FEATURE_NAMES = [
    "hour_of_day",
    "speed_kmh",
    "route_deviation_meters",
    "nearby_incident_count",
    "battery_level",
    "is_isolated_area",
    "lighting_score"
]

def train_and_save_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    if not os.path.exists(DATA_PATH):
        df = generate_synthetic_safety_data(output_path=DATA_PATH)
    else:
        df = pd.read_csv(DATA_PATH)

    X = df[FEATURE_NAMES]
    y = df["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model trained. Accuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred))

    joblib.dump({"model": clf, "features": FEATURE_NAMES, "classes": clf.classes_.tolist()}, MODEL_PATH)
    print(f"Model artifact successfully saved to {MODEL_PATH}")
    return clf

if __name__ == "__main__":
    train_and_save_model()
