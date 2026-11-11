"""
Synthetic Training Dataset Generator for AI Safety Risk Assessment
------------------------------------------------------------------
DISCLAIMER: This dataset contains synthetic simulated data explicitly generated
for educational, research, and project demonstration purposes to model women's
safety risk patterns. No real-world personal victim information is used.
"""

import os
import random
import pandas as pd
import numpy as np

def generate_synthetic_safety_data(num_samples: int = 3000, output_path: str = "backend/app/ml/synthetic_safety_data.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    np.random.seed(42)
    random.seed(42)

    records = []

    # Feature ranges:
    # 1. hour_of_day (0 to 23): Night hours (21:00 - 05:00) increase risk
    # 2. speed_kmh (0 to 80): Unusual prolonged stop (<1 kmh) or running (12-25 kmh)
    # 3. route_deviation_meters (0 to 1500m): Deviations > 250m increase risk
    # 4. nearby_incident_count (0 to 10): Incidents within 1km radius
    # 5. battery_level (5 to 100): Low battery (< 15%) increases vulnerability
    # 6. is_isolated_area (0 or 1): Alleyways, abandoned zones, unlit streets
    # 7. lighting_score (1 to 10): Streetlight rating (1 = pitch black, 10 = brightly illuminated)

    for i in range(num_samples):
        hour = random.randint(0, 23)
        speed = round(random.uniform(0.5, 35.0), 1)
        deviation = round(float(np.random.exponential(scale=120)), 1)
        incidents = int(np.random.poisson(lam=1.5))
        battery = random.randint(5, 100)
        isolated = 1 if random.random() < 0.28 else 0
        lighting = random.randint(1, 10)

        # Risk scoring heuristic to assign ground-truth label
        risk_score = 0

        # Night-time factor
        if hour >= 22 or hour <= 4:
            risk_score += 35
        elif hour >= 19 or hour == 5:
            risk_score += 20
        else:
            risk_score += 5

        # Isolation and lighting factor
        if isolated:
            risk_score += 25
        if lighting <= 3:
            risk_score += 20
        elif lighting <= 6:
            risk_score += 10

        # Incidents factor
        risk_score += min(incidents * 8, 30)

        # Deviation factor
        if deviation > 400:
            risk_score += 25
        elif deviation > 150:
            risk_score += 12

        # Battery factor
        if battery < 15:
            risk_score += 15

        # Add Gaussian noise
        risk_score += np.random.normal(0, 5)
        risk_score = max(0, min(100, risk_score))

        # Assign Category
        if risk_score < 38:
            label = "SAFE"
        elif risk_score < 68:
            label = "WARNING"
        else:
            label = "HIGH RISK"

        records.append({
            "hour_of_day": hour,
            "speed_kmh": speed,
            "route_deviation_meters": deviation,
            "nearby_incident_count": incidents,
            "battery_level": battery,
            "is_isolated_area": isolated,
            "lighting_score": lighting,
            "simulated_risk_score": round(risk_score, 1),
            "risk_label": label,
            "is_synthetic": 1
        })

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Synthetic dataset saved to {output_path} with {len(df)} samples.")
    print(df["risk_label"].value_counts())
    return df

if __name__ == "__main__":
    generate_synthetic_safety_data()
