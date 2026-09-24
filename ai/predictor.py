import os
import joblib
import numpy as np

from ai.db import get_camera_health


# ---------------------------------------------------------
# Load trained Random Forest model
# ---------------------------------------------------------

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "camera_health_model.pkl"
)

model = joblib.load(MODEL_PATH)


# ---------------------------------------------------------
# Predict camera health
# ---------------------------------------------------------

def predict_camera_health(camera_id: int):

    health_data = get_camera_health(camera_id)

    if health_data is None:
        return {
            "success": False,
            "camera_id": camera_id,
            "message": "No health data found for this camera."
        }

    uptime, response_time, packet_loss, cpu_usage = health_data

    # Same feature order used by the trained model
    features = np.array([
        [
            uptime,
            response_time,
            packet_loss,
            cpu_usage
        ]
    ])

    prediction = model.predict(features)[0]

    # Probability, if supported by the Random Forest model
    probability = None

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)[0]
        probability = float(max(probabilities))

    return {
        "success": True,
        "camera_id": camera_id,
        "inputs": {
            "uptime": uptime,
            "response_time": response_time,
            "packet_loss": packet_loss,
            "cpu_usage": cpu_usage
        },
        "prediction": str(prediction),
        "confidence": probability
    }