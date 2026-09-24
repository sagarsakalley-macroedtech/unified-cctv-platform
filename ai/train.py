import os
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


# =========================================================
# PATH
# =========================================================

BASE_DIR = os.path.dirname(__file__)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "camera_health_model.pkl"
)


# =========================================================
# CREATE SYNTHETIC CCTV HEALTH DATA
# =========================================================

np.random.seed(42)

number_of_records = 1000

data = pd.DataFrame({

    "uptime": np.random.uniform(
        70, 100, number_of_records
    ),

    "response_time": np.random.uniform(
        50, 1000, number_of_records
    ),

    "packet_loss": np.random.uniform(
        0, 20, number_of_records
    ),

    "cpu_usage": np.random.uniform(
        10, 100, number_of_records
    )
})


# =========================================================
# CREATE HEALTH LABEL
# =========================================================

def calculate_health(row):

    if (
        row["uptime"] >= 95
        and row["response_time"] < 300
        and row["packet_loss"] < 5
        and row["cpu_usage"] < 80
    ):
        return "HEALTHY"

    elif (
        row["uptime"] >= 85
        and row["response_time"] < 600
        and row["packet_loss"] < 10
        and row["cpu_usage"] < 90
    ):
        return "WARNING"

    else:
        return "CRITICAL"


data["health"] = data.apply(
    calculate_health,
    axis=1
)


# =========================================================
# FEATURES
# =========================================================

X = data[
    [
        "uptime",
        "response_time",
        "packet_loss",
        "cpu_usage"
    ]
]

y = data["health"]


# =========================================================
# TRAIN / TEST SPLIT
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# =========================================================
# CREATE MODEL
# =========================================================

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)


# =========================================================
# TRAIN
# =========================================================

print("Training CCTV Camera Health Model...")

model.fit(
    X_train,
    y_train
)


# =========================================================
# EVALUATION
# =========================================================

predictions = model.predict(
    X_test
)

accuracy = accuracy_score(
    y_test,
    predictions
)


print()
print("========================================")
print("CCTV AI MODEL TRAINING COMPLETED")
print("========================================")
print(
    f"Training records : {len(X_train)}"
)
print(
    f"Testing records  : {len(X_test)}"
)
print(
    f"Accuracy         : {accuracy:.2%}"
)


# =========================================================
# SAVE MODEL
# =========================================================

joblib.dump(
    model,
    MODEL_PATH
)


print(
    f"Model saved to   : {MODEL_PATH}"
)

print("========================================")