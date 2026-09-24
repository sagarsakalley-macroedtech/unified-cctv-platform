from pathlib import Path
import pickle
import traceback

import numpy as np

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"]
)


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


MODEL_PATH = (
    PROJECT_ROOT
    / "ai"
    / "camera_health_model.pkl"
)


# =========================================================
# MODEL
# =========================================================

MODEL = None


def get_model():

    global MODEL

    if MODEL is not None:

        return MODEL


    if not MODEL_PATH.exists():

        raise FileNotFoundError(

            f"ML model not found: "
            f"{MODEL_PATH}"

        )


    with open(
        MODEL_PATH,
        "rb"
    ) as model_file:

        MODEL = pickle.load(
            model_file
        )


    return MODEL


# =========================================================
# HEALTH STATUS
# =========================================================

def convert_prediction(
    prediction
):

    try:

        if hasattr(
            prediction,
            "item"
        ):

            prediction = (
                prediction.item()
            )

    except Exception:

        pass


    if isinstance(
        prediction,
        str
    ):

        value = (
            prediction
            .strip()
            .lower()
        )


        if "healthy" in value:

            return "Healthy"


        if "warning" in value:

            return "Warning"


        if "critical" in value:

            return "Critical"


        return prediction


    try:

        numeric_prediction = int(
            prediction
        )


        # Model mapping
        if numeric_prediction == 0:

            return "Critical"


        if numeric_prediction == 1:

            return "Warning"


        if numeric_prediction == 2:

            return "Healthy"


    except Exception:

        pass


    return "Unknown"


# =========================================================
# HEALTH SCORE
# =========================================================

def calculate_health_score(

    uptime,

    response_time,

    packet_loss,

    cpu_usage

):

    uptime_score = max(

        0,

        min(
            100,
            float(uptime)
        )

    )


    response_score = max(

        0,

        min(

            100,

            100
            -
            (
                float(response_time)
                / 5
            )

        )

    )


    packet_score = max(

        0,

        min(

            100,

            100
            -
            (
                float(packet_loss)
                * 10
            )

        )

    )


    cpu_score = max(

        0,

        min(

            100,

            100
            -
            (
                max(
                    0,
                    float(cpu_usage)
                    - 70
                )
                * 2
            )

        )

    )


    score = (

        uptime_score
        * 0.40

        +

        response_score
        * 0.20

        +

        packet_score
        * 0.20

        +

        cpu_score
        * 0.20

    )


    return round(

        max(
            0,
            min(
                100,
                score
            )
        ),

        2

    )


# =========================================================
# AI CAMERA HEALTH
# =========================================================

@router.post(
    "/camera-health"
)
def camera_health_prediction(

    payload: dict,

    db: Session = Depends(
        get_db
    )

):

    try:

        required_fields = [

            "camera_id",

            "uptime",

            "response_time",

            "packet_loss",

            "cpu_usage"

        ]


        missing_fields = [

            field

            for field
            in required_fields

            if field not in payload

        ]


        if missing_fields:

            return {

                "success": False,

                "error":
                    "Missing required fields: "
                    +
                    ", ".join(
                        missing_fields
                    )

            }


        camera_id = int(

            payload[
                "camera_id"
            ]

        )


        uptime = float(

            payload[
                "uptime"
            ]

        )


        response_time = float(

            payload[
                "response_time"
            ]

        )


        packet_loss = float(

            payload[
                "packet_loss"
            ]

        )


        cpu_usage = float(

            payload[
                "cpu_usage"
            ]

        )


        # =================================================
        # LOAD RANDOM FOREST MODEL
        # =================================================

        model = get_model()


        # =================================================
        # MODEL INPUT
        # =================================================

        features = np.array(

            [[

                uptime,

                response_time,

                packet_loss,

                cpu_usage

            ]],

            dtype=float

        )


        # =================================================
        # RANDOM FOREST PREDICTION
        # =================================================

        prediction = model.predict(

            features

        )[0]


        health_status = (
            convert_prediction(
                prediction
            )
        )


        # =================================================
        # CONFIDENCE
        # =================================================

        confidence = None


        if hasattr(

            model,

            "predict_proba"

        ):

            try:

                probabilities = (
                    model.predict_proba(
                        features
                    )[0]
                )


                confidence = round(

                    float(
                        np.max(
                            probabilities
                        )
                    )
                    * 100,

                    2

                )

            except Exception:

                confidence = None


        # =================================================
        # HEALTH SCORE
        # =================================================

        health_score = (
            calculate_health_score(

                uptime,

                response_time,

                packet_loss,

                cpu_usage

            )
        )


        # =================================================
        # SAVE TO POSTGRESQL
        # =================================================

        insert_query = text(

            """

            INSERT INTO camera_health

            (

                camera_id,

                uptime,

                response_time,

                packet_loss,

                cpu_usage,

                health_status,

                health_score

            )

            VALUES

            (

                :camera_id,

                :uptime,

                :response_time,

                :packet_loss,

                :cpu_usage,

                :health_status,

                :health_score

            )

            """

        )


        db.execute(

            insert_query,

            {

                "camera_id":
                    camera_id,

                "uptime":
                    uptime,

                "response_time":
                    response_time,

                "packet_loss":
                    packet_loss,

                "cpu_usage":
                    cpu_usage,

                "health_status":
                    health_status,

                "health_score":
                    health_score

            }

        )


        db.commit()


        # =================================================
        # RESPONSE
        # =================================================

        return {

            "success": True,

            "camera_id":
                camera_id,

            "prediction": {

                "health_status":
                    health_status,

                "health_score":
                    health_score,

                "confidence":
                    confidence

            },

            "metrics": {

                "uptime":
                    uptime,

                "response_time":
                    response_time,

                "packet_loss":
                    packet_loss,

                "cpu_usage":
                    cpu_usage

            },

            "model": {

                "name":
                    "Random Forest",

                "type":
                    "RandomForestClassifier"

            }

        }


    except Exception as e:

        try:

            db.rollback()

        except Exception:

            pass


        print(
            "AI CAMERA HEALTH ERROR"
        )

        traceback.print_exc()


        return {

            "success": False,

            "error":
                str(e),

            "error_type":
                type(e).__name__

        }