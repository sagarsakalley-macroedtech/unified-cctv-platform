# =========================================================
# GUJARAT CCTV REGISTRY
# MODEL 01
# FastAPI Backend
# CCTV Registry + GIS + Health Monitoring + AI
# =========================================================

import os
import traceback
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from .db import get_db
from .resource_client import (
    get_resource_status,
    get_camera_catalogue
)


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="Unified CCTV Platform API",
    description=(
        "Centralised CCTV Registry, GIS Mapping, "
        "Camera Health Monitoring and AI Prediction Platform"
    ),
    version="2.0.0"
)


# =========================================================
# PATH CONFIGURATION
# =========================================================

BACKEND_DIR = Path(__file__).resolve().parent

PROJECT_DIR = BACKEND_DIR.parent

MODEL_PATH = Path(
    os.getenv(
        "CAMERA_HEALTH_MODEL",
        str(
            PROJECT_DIR
            / "ai"
            / "camera_health_model.pkl"
        )
    )
)


# =========================================================
# AI MODEL CACHE
# =========================================================

MODEL = None


def load_model():

    global MODEL

    if MODEL is not None:
        return MODEL

    if not MODEL_PATH.exists():

        raise HTTPException(
            status_code=500,
            detail={
                "message": "AI model file not found",
                "model_path": str(MODEL_PATH)
            }
        )

    try:

        MODEL = joblib.load(
            MODEL_PATH
        )

        return MODEL

    except Exception as e:

        print(
            traceback.format_exc()
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "AI model could not be loaded",
                "error": str(e),
                "model_path": str(MODEL_PATH)
            }
        )


# =========================================================
# DATABASE COLUMN HELPER
# =========================================================

def get_table_columns(
    db: Session,
    table_name: str
):

    try:

        result = db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = :table_name
                ORDER BY ordinal_position
                """
            ),
            {
                "table_name": table_name
            }
        )

        return [
            row[0]
            for row in result.fetchall()
        ]

    except Exception:

        return []


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Gujarat CCTV Registry API is running",
        "status": "online",
        "version": "2.0.0",
        "ai_enabled": MODEL_PATH.exists()
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check(
    db: Session = Depends(get_db)
):

    try:

        db.execute(
            text("SELECT 1")
        )

        return {
            "status": "healthy",
            "database": "connected",
            "ai_model": (
                "available"
                if MODEL_PATH.exists()
                else "not_found"
            )
        }

    except Exception as e:

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "ai_model": (
                "available"
                if MODEL_PATH.exists()
                else "not_found"
            ),
            "error": str(e)
        }


# =========================================================
# AI MODEL STATUS
# =========================================================

@app.get("/api/ai/status")
def ai_status():

    if not MODEL_PATH.exists():

        return {
            "available": False,
            "model": None,
            "model_path": str(MODEL_PATH),
            "message": "Model file does not exist"
        }

    try:

        model = load_model()

        return {
            "available": True,
            "model": type(model).__name__,
            "model_path": str(MODEL_PATH),
            "message": "AI model loaded successfully"
        }

    except HTTPException as e:

        return {
            "available": False,
            "model": None,
            "model_path": str(MODEL_PATH),
            "message": e.detail
        }

    except Exception as e:

        return {
            "available": False,
            "model": None,
            "model_path": str(MODEL_PATH),
            "error": str(e)
        }


# =========================================================
# DASHBOARD
# =========================================================

@app.get("/api/dashboard")
def dashboard(
    db: Session = Depends(get_db)
):

    response = {
        "departments": 0,
        "vms_systems": 0,
        "total_cameras": 0,
        "online_cameras": 0,
        "offline_cameras": 0
    }

    try:

        # -------------------------------------------------
        # DEPARTMENTS
        # -------------------------------------------------

        department_columns = get_table_columns(
            db,
            "departments"
        )

        if department_columns:

            result = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM departments
                    """
                )
            )

            response["departments"] = (
                result.scalar() or 0
            )


        # -------------------------------------------------
        # VMS
        # -------------------------------------------------

        vms_columns = get_table_columns(
            db,
            "vms_systems"
        )

        if vms_columns:

            result = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM vms_systems
                    """
                )
            )

            response["vms_systems"] = (
                result.scalar() or 0
            )


        # -------------------------------------------------
        # CAMERAS
        # -------------------------------------------------

        camera_columns = get_table_columns(
            db,
            "cameras"
        )

        if not camera_columns:

            return response


        result = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM cameras
                """
            )
        )

        response["total_cameras"] = (
            result.scalar() or 0
        )


        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        if "status" in camera_columns:

            result = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM cameras
                    WHERE UPPER(CAST(status AS TEXT))
                    = 'ONLINE'
                    """
                )
            )

            response["online_cameras"] = (
                result.scalar() or 0
            )


            result = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM cameras
                    WHERE UPPER(CAST(status AS TEXT))
                    = 'OFFLINE'
                    """
                )
            )

            response["offline_cameras"] = (
                result.scalar() or 0
            )


        return response


    except Exception as e:

        response["error"] = str(e)

        return response


# =========================================================
# CAMERA REGISTRY
# =========================================================

@app.get("/api/cameras")
def get_cameras(
    db: Session = Depends(get_db)
):

    try:

        columns = get_table_columns(
            db,
            "cameras"
        )

        if not columns:

            return []


        # -------------------------------------------------
        # SAFE COLUMN SELECTION
        # -------------------------------------------------

        preferred_columns = [
            "camera_id",
            "camera_code",
            "vms_id",
            "camera_name",
            "location",
            "city",
            "district",
            "latitude",
            "longitude",
            "protocol",
            "stream_url",
            "status",
            "camera_type"
        ]


        selected_columns = [
            column
            for column in preferred_columns
            if column in columns
        ]


        if not selected_columns:

            # Fallback:
            # return all columns
            selected_columns = columns


        select_sql = ", ".join(
            f'"{column}"'
            for column in selected_columns
        )


        order_column = (
            "camera_id"
            if "camera_id" in columns
            else selected_columns[0]
        )


        query = f"""
            SELECT {select_sql}
            FROM cameras
            ORDER BY "{order_column}"
        """


        result = db.execute(
            text(query)
        )


        return [
            dict(row)
            for row in result.mappings().all()
        ]


    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# SINGLE CAMERA
# =========================================================

@app.get("/api/cameras/{camera_id}")
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db)
):

    try:

        columns = get_table_columns(
            db,
            "cameras"
        )

        if "camera_id" not in columns:

            raise HTTPException(
                status_code=500,
                detail="camera_id column not found in cameras table"
            )


        selected_columns = [
            column
            for column in [
                "camera_id",
                "camera_code",
                "vms_id",
                "camera_name",
                "location",
                "city",
                "district",
                "latitude",
                "longitude",
                "protocol",
                "stream_url",
                "status",
                "camera_type"
            ]
            if column in columns
        ]


        select_sql = ", ".join(
            f'"{column}"'
            for column in selected_columns
        )


        result = db.execute(
            text(
                f"""
                SELECT {select_sql}
                FROM cameras
                WHERE camera_id = :camera_id
                """
            ),
            {
                "camera_id": camera_id
            }
        )


        row = result.mappings().first()


        if row is None:

            raise HTTPException(
                status_code=404,
                detail="Camera not found"
            )


        return dict(row)


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# DEPARTMENTS
# =========================================================

@app.get("/api/departments")
def get_departments(
    db: Session = Depends(get_db)
):

    try:

        columns = get_table_columns(
            db,
            "departments"
        )

        if not columns:

            return []


        order_column = (
            "department_id"
            if "department_id" in columns
            else columns[0]
        )


        result = db.execute(
            text(
                f"""
                SELECT *
                FROM departments
                ORDER BY "{order_column}"
                """
            )
        )


        return [
            dict(row)
            for row in result.mappings().all()
        ]


    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# VMS SYSTEMS
# =========================================================

@app.get("/api/vms")
def get_vms_systems(
    db: Session = Depends(get_db)
):

    try:

        columns = get_table_columns(
            db,
            "vms_systems"
        )

        if not columns:

            return []


        order_column = (
            "vms_id"
            if "vms_id" in columns
            else columns[0]
        )


        result = db.execute(
            text(
                f"""
                SELECT *
                FROM vms_systems
                ORDER BY "{order_column}"
                """
            )
        )


        return [
            dict(row)
            for row in result.mappings().all()
        ]


    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# DISTRICTS / CITIES
# =========================================================

@app.get("/api/districts")
def get_districts(
    db: Session = Depends(get_db)
):

    try:

        columns = get_table_columns(
            db,
            "cameras"
        )

        if "city" not in columns:

            return []


        result = db.execute(
            text(
                """
                SELECT DISTINCT city
                FROM cameras
                WHERE city IS NOT NULL
                ORDER BY city
                """
            )
        )


        return [
            {
                "city": row[0]
            }
            for row in result.fetchall()
        ]


    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# GIS CAMERA DATA
# =========================================================

@app.get("/api/gis")
def get_gis_data(
    db: Session = Depends(get_db)
):

    try:

        columns = get_table_columns(
            db,
            "cameras"
        )


        required = [
            "latitude",
            "longitude"
        ]


        if not all(
            column in columns
            for column in required
        ):

            return []


        preferred_columns = [
            "camera_id",
            "camera_code",
            "camera_name",
            "location",
            "city",
            "district",
            "latitude",
            "longitude",
            "status"
        ]


        selected_columns = [
            column
            for column in preferred_columns
            if column in columns
        ]


        select_sql = ", ".join(
            f'"{column}"'
            for column in selected_columns
        )


        order_column = (
            "camera_id"
            if "camera_id" in columns
            else selected_columns[0]
        )


        query = f"""
            SELECT {select_sql}
            FROM cameras
            WHERE latitude IS NOT NULL
            AND longitude IS NOT NULL
            ORDER BY "{order_column}"
        """


        result = db.execute(
            text(query)
        )


        return [
            dict(row)
            for row in result.mappings().all()
        ]


    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# CAMERA HEALTH
# =========================================================

@app.get("/api/cameras/health")
def camera_health(
    db: Session = Depends(get_db)
):

    try:

        columns = get_table_columns(
            db,
            "camera_health"
        )

        if not columns:

            return []


        order_column = (
            "prediction_time"
            if "prediction_time" in columns
            else columns[0]
        )


        result = db.execute(
            text(
                f"""
                SELECT *
                FROM camera_health
                ORDER BY "{order_column}" DESC
                """
            )
        )


        return [
            dict(row)
            for row in result.mappings().all()
        ]


    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# AI REQUEST MODEL
# =========================================================

class CameraHealthRequest(BaseModel):

    camera_id: int = Field(
        ...,
        description="Camera ID"
    )

    uptime: float = Field(
        ...,
        ge=0,
        le=100
    )

    response_time: float = Field(
        ...,
        ge=0
    )

    packet_loss: float = Field(
        ...,
        ge=0,
        le=100
    )

    cpu_usage: float = Field(
        ...,
        ge=0,
        le=100
    )


# =========================================================
# AI CAMERA HEALTH PREDICTION
# =========================================================

@app.post("/api/ai/camera-health")
def predict_camera_health(
    request: CameraHealthRequest,
    db: Session = Depends(get_db)
):

    try:

        # =================================================
        # LOAD MODEL
        # =================================================

        model = load_model()


        # =================================================
        # FEATURES
        # =================================================

        features = np.array(
            [[
                float(request.uptime),
                float(request.response_time),
                float(request.packet_loss),
                float(request.cpu_usage)
            ]],
            dtype=float
        )


        # =================================================
        # PREDICTION
        # =================================================

        try:

            prediction = model.predict(
                features
            )[0]

        except Exception as e:

            print(
                "\n========== AI MODEL ERROR =========="
            )

            print(
                traceback.format_exc()
            )

            print(
                "===================================="
            )

            raise HTTPException(
                status_code=500,
                detail={
                    "message": "AI prediction failed",
                    "error": str(e),
                    "model_type": type(model).__name__,
                    "model_path": str(MODEL_PATH),
                    "features": [
                        "uptime",
                        "response_time",
                        "packet_loss",
                        "cpu_usage"
                    ]
                }
            )


        # =================================================
        # PROBABILITY
        # =================================================

        probability = None

        try:

            probabilities = model.predict_proba(
                features
            )[0]

            probability = round(
                float(
                    np.max(probabilities) * 100
                ),
                2
            )

        except Exception:

            probability = None


        # =================================================
        # STATUS
        # =================================================

        raw_prediction = str(
            prediction
        ).strip()


        prediction_lower = (
            raw_prediction.lower()
        )


        if prediction_lower in [
            "1",
            "healthy",
            "good",
            "normal",
            "online"
        ]:

            health_status = "Healthy"


        elif prediction_lower in [
            "2",
            "warning",
            "moderate",
            "degraded"
        ]:

            health_status = "Warning"


        elif prediction_lower in [
            "0",
            "critical",
            "bad",
            "failure",
            "failed",
            "offline"
        ]:

            health_status = "Critical"


        else:

            health_status = raw_prediction


        # =================================================
        # HEALTH SCORE
        # =================================================

        if probability is not None:

            health_score = probability

        else:

            uptime_score = float(
                request.uptime
            )

            response_score = max(
                0,
                100 - (
                    float(request.response_time)
                    / 10
                )
            )

            packet_score = max(
                0,
                100 - (
                    float(request.packet_loss)
                    * 10
                )
            )

            cpu_score = max(
                0,
                100 - float(
                    request.cpu_usage
                )
            )

            health_score = round(
                (
                    uptime_score
                    + response_score
                    + packet_score
                    + cpu_score
                ) / 4,
                2
            )


        # =================================================
        # DATABASE SAVE
        # =================================================

        health_columns = get_table_columns(
            db,
            "camera_health"
        )


        if not health_columns:

            raise HTTPException(
                status_code=500,
                detail=(
                    "camera_health table was not found."
                )
            )


        # -------------------------------------------------
        # ONLY USE COLUMNS THAT ACTUALLY EXIST
        # -------------------------------------------------

        insert_columns = []

        insert_values = {}

        if "camera_id" in health_columns:

            insert_columns.append(
                "camera_id"
            )

            insert_values[
                "camera_id"
            ] = int(
                request.camera_id
            )


        if "uptime" in health_columns:

            insert_columns.append(
                "uptime"
            )

            insert_values[
                "uptime"
            ] = float(
                request.uptime
            )


        if "response_time" in health_columns:

            insert_columns.append(
                "response_time"
            )

            insert_values[
                "response_time"
            ] = float(
                request.response_time
            )


        if "packet_loss" in health_columns:

            insert_columns.append(
                "packet_loss"
            )

            insert_values[
                "packet_loss"
            ] = float(
                request.packet_loss
            )


        if "cpu_usage" in health_columns:

            insert_columns.append(
                "cpu_usage"
            )

            insert_values[
                "cpu_usage"
            ] = float(
                request.cpu_usage
            )


        if "health_status" in health_columns:

            insert_columns.append(
                "health_status"
            )

            insert_values[
                "health_status"
            ] = health_status


        if "health_score" in health_columns:

            insert_columns.append(
                "health_score"
            )

            insert_values[
                "health_score"
            ] = float(
                health_score
            )


        # -------------------------------------------------
        # INSERT
        # -------------------------------------------------

        saved_record = None


        if insert_columns:

            column_sql = ", ".join(
                f'"{column}"'
                for column in insert_columns
            )


            value_sql = ", ".join(
                f":{column}"
                for column in insert_columns
            )


            returning_sql = ""


            if "id" in health_columns:

                returning_sql = """
                    RETURNING id
                """


            query = f"""
                INSERT INTO camera_health (
                    {column_sql}
                )
                VALUES (
                    {value_sql}
                )
                {returning_sql}
            """


            result = db.execute(
                text(query),
                insert_values
            )


            if "id" in health_columns:

                saved_record = (
                    result.mappings().first()
                )


            db.commit()


        # =================================================
        # RESPONSE
        # =================================================

        return {

            "success": True,

            "camera": {
                "camera_id": int(
                    request.camera_id
                )
            },

            "input": {

                "uptime": float(
                    request.uptime
                ),

                "response_time": float(
                    request.response_time
                ),

                "packet_loss": float(
                    request.packet_loss
                ),

                "cpu_usage": float(
                    request.cpu_usage
                )
            },

            "prediction": {

                "status": health_status,

                "raw_prediction": raw_prediction,

                "probability": probability,

                "health_score": health_score
            },

            "model": {

                "type": type(
                    model
                ).__name__,

                "path": str(
                    MODEL_PATH
                )
            },

            "database": {

                "saved": True,

                "record_id": (
                    saved_record.get("id")
                    if saved_record
                    else None
                )
            }
        }


    except HTTPException:

        try:
            db.rollback()
        except Exception:
            pass

        raise


    except Exception as e:

        try:
            db.rollback()
        except Exception:
            pass


        print(
            "\n========== CAMERA HEALTH ERROR =========="
        )

        print(
            traceback.format_exc()
        )

        print(
            "=========================================\n"
        )


        raise HTTPException(
            status_code=500,
            detail={
                "message": "Camera health prediction failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


# =========================================================
# AI HEALTH HISTORY
# =========================================================

@app.get("/api/ai/camera-health/{camera_id}")
def get_camera_ai_health_history(
    camera_id: int,
    db: Session = Depends(get_db)
):

    try:

        columns = get_table_columns(
            db,
            "camera_health"
        )

        if "camera_id" not in columns:

            return {
                "camera_id": camera_id,
                "count": 0,
                "records": []
            }


        order_column = (
            "prediction_time"
            if "prediction_time" in columns
            else "id"
            if "id" in columns
            else "camera_id"
        )


        result = db.execute(
            text(
                f"""
                SELECT *
                FROM camera_health
                WHERE camera_id = :camera_id
                ORDER BY "{order_column}" DESC
                """
            ),
            {
                "camera_id": camera_id
            }
        )


        records = [
            dict(row)
            for row in result.mappings().all()
        ]


        return {
            "camera_id": camera_id,
            "count": len(records),
            "records": records
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# CCTV RESOURCE SERVICE STATUS
# =========================================================

@app.get("/api/resources/status")
def resource_status():

    try:

        return get_resource_status()

    except Exception as e:

        return {
            "available": False,
            "error": str(e)
        }


# =========================================================
# CCTV RESOURCE CAMERA CATALOGUE
# =========================================================

@app.get("/api/resources/catalogue")
def resource_catalogue():

    try:

        return get_camera_catalogue()

    except Exception as e:

        return {
            "available": False,
            "cameras": [],
            "error": str(e)
        }


# =========================================================
# RESOURCE TEST
# =========================================================

@app.get("/api/resources/test")
def resource_test():

    try:

        status = get_resource_status()

        return {
            "service": "CCTV Resource Service",
            "available": status.get(
                "available",
                False
            ),
            "status_code": status.get(
                "status_code"
            ),
            "url": status.get(
                "url"
            )
        }

    except Exception as e:

        return {
            "service": "CCTV Resource Service",
            "available": False,
            "error": str(e)
        }


# =========================================================
# DATABASE STRUCTURE DEBUG
# =========================================================

@app.get("/api/debug/database")
def database_structure(
    db: Session = Depends(get_db)
):

    return {
        "cameras": get_table_columns(
            db,
            "cameras"
        ),

        "camera_health": get_table_columns(
            db,
            "camera_health"
        ),

        "departments": get_table_columns(
            db,
            "departments"
        ),

        "vms_systems": get_table_columns(
            db,
            "vms_systems"
        )
    }