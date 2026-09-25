# =========================================================
# UNIFIED CCTV CONTROL ROOM
# MODEL 02
# Unified Viewing + CCTV Analytics
# Gujarat Police Hackathon 2026
# =========================================================

import os
import time
from pathlib import Path

import cv2
import joblib
import numpy as np
import pandas as pd
import requests
import streamlit as st
import folium

from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from sklearn.ensemble import RandomForestClassifier


# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Unified CCTV Control Room",
    page_icon="📹",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
)

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent

# ---------------------------------------------------------
# VIDEO LOCATIONS
# ---------------------------------------------------------

VIDEO_CANDIDATES = [
    APP_DIR / "media" / "cctv_demo.mp4",
    PROJECT_DIR / "media" / "cctv_demo.mp4",
    APP_DIR / "cctv_demo.mp4",
    PROJECT_DIR / "cctv_demo.mp4",
]

VIDEO_PATH = None

for candidate in VIDEO_CANDIDATES:
    if candidate.exists():
        VIDEO_PATH = candidate
        break


# ---------------------------------------------------------
# MODEL LOCATIONS
# ---------------------------------------------------------

MODEL_CANDIDATES = [
    APP_DIR / "models" / "camera_health_model.pkl",
    PROJECT_DIR / "models" / "camera_health_model.pkl",
    APP_DIR / "camera_health_model.pkl",
    PROJECT_DIR / "camera_health_model.pkl",
]

MODEL_PATH = None

for candidate in MODEL_CANDIDATES:
    if candidate.exists():
        MODEL_PATH = candidate
        break


MODEL_DIR = APP_DIR / "models"

if not MODEL_DIR.exists():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 38px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .sub-title {
        font-size: 18px;
        color: #8b949e;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 27px;
        font-weight: 700;
        margin-top: 10px;
    }

    .status-card {
        padding: 18px;
        border-radius: 12px;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .ai-card {
        padding: 20px;
        border-radius: 12px;
        background: #161b22;
        border: 1px solid #30363d;
    }

    .video-card {
        padding: 15px;
        border-radius: 12px;
        background: #161b22;
        border: 1px solid #30363d;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# API FUNCTIONS
# =========================================================

def get_api_data(endpoint, show_error=False):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        if show_error:
            st.warning(
                f"FastAPI endpoint unavailable: {endpoint}"
            )

        return None


# =========================================================
# NORMALIZE CAMERA DATA
# =========================================================

def normalize_camera_data(data):

    if data is None:
        return pd.DataFrame()

    if isinstance(data, dict):

        if isinstance(data.get("data"), list):
            data = data["data"]

        elif isinstance(data.get("cameras"), list):
            data = data["cameras"]

        elif isinstance(data.get("results"), list):
            data = data["results"]

        else:
            return pd.DataFrame()

    if not isinstance(data, list):
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if df.empty:
        return df

    # -----------------------------------------------------
    # STANDARD COLUMN NAMES
    # -----------------------------------------------------

    aliases = {

        "id": "camera_id",

        "cameraId": "camera_id",

        "camera_code": "camera_code",

        "cameraCode": "camera_code",

        "name": "camera_name",

        "cameraName": "camera_name",

        "lat": "latitude",

        "lng": "longitude",

        "lon": "longitude",

        "status": "status",

        "operational_status": "status",

    }

    for old_name, new_name in aliases.items():

        if (
            old_name in df.columns
            and new_name not in df.columns
        ):

            df[new_name] = df[old_name]

    # -----------------------------------------------------
    # DEFAULT COLUMNS
    # -----------------------------------------------------

    defaults = {

        "camera_id": range(1, len(df) + 1),

        "camera_code": "N/A",

        "camera_name": "CCTV Camera",

        "location": "N/A",

        "city": "N/A",

        "protocol": "N/A",

        "status": "UNKNOWN",

        "latitude": np.nan,

        "longitude": np.nan,

    }

    for column, default_value in defaults.items():

        if column not in df.columns:

            if hasattr(default_value, "__iter__") and not isinstance(
                default_value,
                str
            ):

                df[column] = list(default_value)

            else:

                df[column] = default_value

    return df


# =========================================================
# LOAD CAMERAS
# =========================================================

camera_data = get_api_data(
    "/api/cameras",
    show_error=False
)

camera_df = normalize_camera_data(camera_data)


# =========================================================
# FALLBACK CAMERA DATA
# =========================================================

if camera_df.empty:

    csv_candidates = [

        PROJECT_DIR / "data" / "cameras.csv",

        APP_DIR / "data" / "cameras.csv",

        PROJECT_DIR / "frontend" / "data" / "cameras.csv",

    ]

    for csv_path in csv_candidates:

        if csv_path.exists():

            try:

                camera_df = pd.read_csv(
                    csv_path
                )

                camera_df = normalize_camera_data(
                    camera_df.to_dict(
                        orient="records"
                    )
                )

                break

            except Exception:
                pass


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">'
    'Unified CCTV Control Room'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Centralised CCTV viewing, monitoring, GIS and AI-based camera health analytics'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    "## Camera Filters"
)

st.sidebar.divider()


# =========================================================
# CITY FILTER
# =========================================================

cities = []

if (
    not camera_df.empty
    and "city" in camera_df.columns
):

    cities = sorted(
        camera_df["city"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


selected_city = st.sidebar.selectbox(
    "City",
    ["All"] + cities
)


# =========================================================
# STATUS FILTER
# =========================================================

statuses = []

if (
    not camera_df.empty
    and "status" in camera_df.columns
):

    statuses = sorted(
        camera_df["status"]
        .dropna()
        .astype(str)
        .str.upper()
        .unique()
        .tolist()
    )


selected_status = st.sidebar.selectbox(
    "Camera Status",
    ["All"] + statuses
)


# =========================================================
# SEARCH
# =========================================================

search_text = st.sidebar.text_input(
    "Search Camera",
    placeholder="Enter camera name or code"
)


# =========================================================
# APPLY FILTERS
# =========================================================

filtered_df = camera_df.copy()

if (
    not filtered_df.empty
    and selected_city != "All"
):

    filtered_df = filtered_df[
        filtered_df["city"]
        .astype(str)
        == selected_city
    ]


if (
    not filtered_df.empty
    and selected_status != "All"
):

    filtered_df = filtered_df[
        filtered_df["status"]
        .astype(str)
        .str.upper()
        == selected_status
    ]


if (
    search_text
    and not filtered_df.empty
):

    search_text_lower = (
        search_text
        .strip()
        .lower()
    )

    name_match = (
        filtered_df["camera_name"]
        .astype(str)
        .str.lower()
        .str.contains(
            search_text_lower,
            na=False
        )
    )

    code_match = (
        filtered_df["camera_code"]
        .astype(str)
        .str.lower()
        .str.contains(
            search_text_lower,
            na=False
        )
    )

    filtered_df = filtered_df[
        name_match | code_match
    ]


# =========================================================
# KPI
# =========================================================

total_cameras = len(camera_df)

online_cameras = 0
offline_cameras = 0

if not camera_df.empty:

    online_cameras = int(
        (
            camera_df["status"]
            .astype(str)
            .str.upper()
            == "ONLINE"
        ).sum()
    )

    offline_cameras = int(
        (
            camera_df["status"]
            .astype(str)
            .str.upper()
            == "OFFLINE"
        ).sum()
    )


k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Total Cameras",
        total_cameras
    )

with k2:
    st.metric(
        "Online",
        online_cameras
    )

with k3:
    st.metric(
        "Offline",
        offline_cameras
    )

with k4:
    st.metric(
        "Filtered",
        len(filtered_df)
    )


# =========================================================
# CAMERA MONITORING
# =========================================================

st.divider()

st.subheader(
    "Camera Monitoring"
)

st.write(
    f"Showing **{len(filtered_df)}** cameras "
    f"out of **{len(camera_df)}**"
)


if not filtered_df.empty:

    display_columns = [

        "camera_id",

        "camera_code",

        "camera_name",

        "location",

        "city",

        "protocol",

        "status"

    ]

    available_columns = [

        column
        for column in display_columns
        if column in filtered_df.columns

    ]

    st.dataframe(
        filtered_df[
            available_columns
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No cameras match the selected filters."
    )


# =========================================================
# AI CAMERA HEALTH PREDICTION
# =========================================================

st.divider()

st.subheader(
    "AI Camera Health Prediction"
)

st.caption(
    "Random Forest based camera health prediction "
    "using uptime, response time, packet loss and CPU usage."
)


# =========================================================
# HEALTH DATA
# =========================================================

health_data = get_api_data(
    "/api/cameras/health",
    show_error=False
)


if isinstance(
    health_data,
    dict
):

    if isinstance(
        health_data.get("data"),
        list
    ):

        health_data = health_data["data"]

    elif isinstance(
        health_data.get("health"),
        list
    ):

        health_data = health_data["health"]

    else:

        health_data = []


if not isinstance(
    health_data,
    list
):

    health_data = []


health_df = pd.DataFrame(
    health_data
)


# =========================================================
# CAMERA OPTIONS
# =========================================================

if not filtered_df.empty:

    ai_camera_ids = (
        filtered_df["camera_id"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

else:

    ai_camera_ids = []


if not ai_camera_ids:

    ai_camera_ids = ["1"]


selected_ai_camera = st.selectbox(
    "Select Camera for AI Prediction",
    ai_camera_ids,
    key="ai_camera_selector"
)


# =========================================================
# FIND HEALTH RECORD
# =========================================================

health_record = None


if not health_df.empty:

    possible_id_columns = [

        "camera_id",

        "cameraId",

        "id"

    ]

    id_column = None

    for column in possible_id_columns:

        if column in health_df.columns:

            id_column = column
            break


    if id_column:

        matches = health_df[
            health_df[id_column]
            .astype(str)
            == str(selected_ai_camera)
        ]

        if not matches.empty:

            health_record = matches.iloc[0]


# =========================================================
# DEFAULT VALUES
# =========================================================

default_uptime = 98.0
default_response = 180.0
default_packet_loss = 1.0
default_cpu = 45.0


if health_record is not None:

    try:

        default_uptime = float(
            health_record.get(
                "uptime",
                default_uptime
            )
        )

    except Exception:
        pass


    try:

        default_response = float(
            health_record.get(
                "response_time",
                default_response
            )
        )

    except Exception:
        pass


    try:

        default_packet_loss = float(
            health_record.get(
                "packet_loss",
                default_packet_loss
            )
        )

    except Exception:
        pass


    try:

        default_cpu = float(
            health_record.get(
                "cpu_usage",
                default_cpu
            )
        )

    except Exception:
        pass


# =========================================================
# PREDICTION INPUT
# =========================================================

input_col1, input_col2, input_col3, input_col4 = (
    st.columns(4)
)


with input_col1:

    uptime = st.number_input(
        "Uptime (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(default_uptime),
        step=0.1,
        key="ai_uptime"
    )


with input_col2:

    response_time = st.number_input(
        "Response Time (ms)",
        min_value=0.0,
        max_value=10000.0,
        value=float(default_response),
        step=10.0,
        key="ai_response"
    )


with input_col3:

    packet_loss = st.number_input(
        "Packet Loss (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(default_packet_loss),
        step=0.1,
        key="ai_packet"
    )


with input_col4:

    cpu_usage = st.number_input(
        "CPU Usage (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(default_cpu),
        step=1.0,
        key="ai_cpu"
    )


# =========================================================
# MODEL CREATION
# =========================================================

def train_demo_model():

    rng = np.random.default_rng(42)

    samples = 2000

    uptime_data = rng.uniform(
        70,
        100,
        samples
    )

    response_data = rng.uniform(
        50,
        1000,
        samples
    )

    packet_data = rng.uniform(
        0,
        20,
        samples
    )

    cpu_data = rng.uniform(
        10,
        100,
        samples
    )

    X = np.column_stack(
        [
            uptime_data,
            response_data,
            packet_data,
            cpu_data
        ]
    )

    health_score = (

        uptime_data * 0.50

        + (100 - np.minimum(
            response_data / 10,
            100
        )) * 0.20

        + (100 - packet_data * 5) * 0.15

        + (100 - cpu_data) * 0.15

    )

    y = np.where(
        health_score >= 70,
        1,
        0
    )

    model = RandomForestClassifier(
        n_estimators=150,
        random_state=42,
        max_depth=8
    )

    model.fit(
        X,
        y
    )

    return model


@st.cache_resource
def load_health_model():

    global MODEL_PATH

    # -----------------------------------------------------
    # TRY EXISTING MODEL
    # -----------------------------------------------------

    if MODEL_PATH is not None:

        try:

            model = joblib.load(
                MODEL_PATH
            )

            return model, "Random Forest Model"

        except Exception:

            pass


    # -----------------------------------------------------
    # CREATE DEMO MODEL
    # -----------------------------------------------------

    model = train_demo_model()

    generated_model_path = (
        MODEL_DIR /
        "camera_health_model.pkl"
    )

    try:

        joblib.dump(
            model,
            generated_model_path
        )

        MODEL_PATH = generated_model_path

    except Exception:

        pass

    return (
        model,
        "Random Forest Demo Model"
    )


# =========================================================
# RUN AI
# =========================================================

run_prediction = st.button(
    "Run AI Health Prediction",
    type="primary",
    key="run_ai_prediction"
)


if run_prediction:

    try:

        model, model_name = (
            load_health_model()
        )

        features = np.array(
            [
                [
                    float(uptime),
                    float(response_time),
                    float(packet_loss),
                    float(cpu_usage)
                ]
            ],
            dtype=float
        )

        prediction = model.predict(
            features
        )[0]

        probability = None

        if hasattr(
            model,
            "predict_proba"
        ):

            probabilities = (
                model.predict_proba(
                    features
                )[0]
            )

            probability = float(
                np.max(
                    probabilities
                ) * 100
            )

        # -------------------------------------------------
        # HEALTH SCORE
        # -------------------------------------------------

        response_score = max(
            0,
            100 -
            (
                min(
                    response_time,
                    1000
                ) / 10
            )
        )

        packet_score = max(
            0,
            100 -
            (
                packet_loss * 5
            )
        )

        cpu_score = max(
            0,
            100 -
            abs(
                cpu_usage - 50
            ) * 1.5
        )

        health_score = (

            uptime * 0.50

            + response_score * 0.20

            + packet_score * 0.15

            + cpu_score * 0.15

        )

        health_score = max(
            0,
            min(
                100,
                health_score
            )
        )

        # -------------------------------------------------
        # HEALTH LABEL
        # -------------------------------------------------

        if prediction == 1:

            health_label = "Healthy"

        else:

            health_label = "Attention Required"


        if health_score >= 80:

            health_label = "Healthy"

        elif health_score >= 60:

            health_label = "Warning"

        else:

            health_label = "Critical"


        st.success(
            f"AI prediction completed for Camera "
            f"{selected_ai_camera}"
        )

        result_col1, result_col2, result_col3 = (
            st.columns(3)
        )

        with result_col1:

            st.metric(
                "Camera Health",
                health_label
            )

        with result_col2:

            st.metric(
                "Health Score",
                f"{health_score:.1f}/100"
            )

        with result_col3:

            if probability is not None:

                st.metric(
                    "Model Confidence",
                    f"{probability:.1f}%"
                )

            else:

                st.metric(
                    "Model Confidence",
                    "N/A"
                )


        st.info(
            f"ML Model: {model_name}"
        )


    except Exception as e:

        # -------------------------------------------------
        # LAST RESORT
        # -------------------------------------------------

        st.error(
            "AI prediction could not be completed."
        )

        st.exception(e)


# =========================================================
# CCTV VIDEO VIEWER + OPENCV
# =========================================================

st.divider()

st.subheader(
    "CCTV Video Viewer"
)

st.caption(
    "OpenCV-enabled CCTV demonstration and video analytics"
)


if VIDEO_PATH is not None:

    video_col, analytics_col = st.columns(
        [2, 1]
    )

    # =====================================================
    # VIDEO
    # =====================================================

    with video_col:

        st.markdown(
            '<div class="video-card">',
            unsafe_allow_html=True
        )

        st.write(
            "**Live / Demo Feed**"
        )

        try:

            with open(
                VIDEO_PATH,
                "rb"
            ) as video_file:

                video_bytes = (
                    video_file.read()
                )

            st.video(
                video_bytes
            )

        except Exception as e:

            st.error(
                f"Unable to display CCTV video: {e}"
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


    # =====================================================
    # OPENCV ANALYTICS
    # =====================================================

    with analytics_col:

        st.markdown(
            '<div class="ai-card">',
            unsafe_allow_html=True
        )

        st.write(
            "### OpenCV Video Analytics"
        )

        cap = cv2.VideoCapture(
            str(VIDEO_PATH)
        )

        if cap.isOpened():

            frame_count = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            fps = float(
                cap.get(
                    cv2.CAP_PROP_FPS
                )
            )

            width = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_WIDTH
                )
            )

            height = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_HEIGHT
                )
            )

            duration = (
                frame_count / fps
                if fps > 0
                else 0
            )

            st.metric(
                "Resolution",
                f"{width} × {height}"
            )

            st.metric(
                "FPS",
                f"{fps:.2f}"
            )

            st.metric(
                "Duration",
                f"{duration:.1f} sec"
            )

            # -------------------------------------------------
            # READ MIDDLE FRAME
            # -------------------------------------------------

            if frame_count > 0:

                middle_frame = int(
                    frame_count / 2
                )

                cap.set(
                    cv2.CAP_PROP_POS_FRAMES,
                    middle_frame
                )

                success, frame = (
                    cap.read()
                )

                if success:

                    gray = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2GRAY
                    )

                    brightness = float(
                        np.mean(gray)
                    )

                    st.metric(
                        "Frame Brightness",
                        f"{brightness:.1f}"
                    )

                    if brightness < 40:

                        lighting_status = (
                            "Low Light"
                        )

                    elif brightness > 210:

                        lighting_status = (
                            "Very Bright"
                        )

                    else:

                        lighting_status = (
                            "Normal"
                        )

                    st.write(
                        "**Lighting:**",
                        lighting_status
                    )


            cap.release()

        else:

            st.warning(
                "OpenCV could not open the CCTV video."
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


else:

    st.warning(
        "cctv_demo.mp4 was not found."
    )

    st.code(
        str(
            APP_DIR /
            "media" /
            "cctv_demo.mp4"
        )
    )


# =========================================================
# OPENCV FRAME ANALYSIS
# =========================================================

if VIDEO_PATH is not None:

    st.divider()

    st.subheader(
        "OpenCV Frame Analysis"
    )

    analyze_video = st.button(
        "Analyze CCTV Video with OpenCV",
        key="opencv_analyze"
    )

    if analyze_video:

        cap = cv2.VideoCapture(
            str(VIDEO_PATH)
        )

        if not cap.isOpened():

            st.error(
                "OpenCV could not open the video."
            )

        else:

            frame_count = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            fps = float(
                cap.get(
                    cv2.CAP_PROP_FPS
                )
            )

            if fps <= 0:
                fps = 25.0

            sample_positions = [

                0,

                int(
                    frame_count * 0.25
                ),

                int(
                    frame_count * 0.50
                ),

                int(
                    frame_count * 0.75
                ),

            ]

            brightness_values = []

            motion_values = []

            previous_gray = None

            for position in sample_positions:

                cap.set(
                    cv2.CAP_PROP_POS_FRAMES,
                    position
                )

                success, frame = (
                    cap.read()
                )

                if not success:
                    continue

                gray = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2GRAY
                )

                brightness = float(
                    np.mean(gray)
                )

                brightness_values.append(
                    brightness
                )

                if previous_gray is not None:

                    difference = cv2.absdiff(
                        previous_gray,
                        gray
                    )

                    motion_score = float(
                        np.mean(difference)
                    )

                    motion_values.append(
                        motion_score
                    )

                previous_gray = gray


            cap.release()


            if brightness_values:

                average_brightness = float(
                    np.mean(
                        brightness_values
                    )
                )

                st.metric(
                    "Average Brightness",
                    f"{average_brightness:.2f}"
                )


            if motion_values:

                average_motion = float(
                    np.mean(
                        motion_values
                    )
                )

                st.metric(
                    "Motion Score",
                    f"{average_motion:.2f}"
                )

                if average_motion > 15:

                    st.success(
                        "OpenCV detected significant frame-to-frame activity."
                    )

                else:

                    st.info(
                        "OpenCV detected relatively low frame-to-frame activity."
                    )


            analysis_df = pd.DataFrame(
                {
                    "Sample Frame":
                        range(
                            1,
                            len(
                                brightness_values
                            ) + 1
                        ),

                    "Brightness":
                        brightness_values
                }
            )

            if not analysis_df.empty:

                st.dataframe(
                    analysis_df,
                    use_container_width=True,
                    hide_index=True
                )


# =========================================================
# GIS MAP
# =========================================================

st.divider()

st.subheader(
    "CCTV GIS Map"
)

st.caption(
    "Geographic distribution of registered CCTV cameras"
)


m = folium.Map(
    location=[
        22.2587,
        71.1924
    ],
    zoom_start=7,
    control_scale=True
)


marker_cluster = (
    MarkerCluster()
    .add_to(m)
)


if not filtered_df.empty:

    for _, row in (
        filtered_df.iterrows()
    ):

        latitude = row.get(
            "latitude"
        )

        longitude = row.get(
            "longitude"
        )

        try:

            latitude = float(
                latitude
            )

            longitude = float(
                longitude
            )

        except Exception:

            continue


        if not (
            np.isfinite(
                latitude
            )
            and
            np.isfinite(
                longitude
            )
        ):

            continue


        camera_name = row.get(
            "camera_name",
            "CCTV Camera"
        )

        camera_code = row.get(
            "camera_code",
            "N/A"
        )

        city = row.get(
            "city",
            "N/A"
        )

        location = row.get(
            "location",
            "N/A"
        )

        status = str(
            row.get(
                "status",
                "UNKNOWN"
            )
        ).upper()


        if status == "ONLINE":

            marker_color = "green"

        elif status == "OFFLINE":

            marker_color = "red"

        else:

            marker_color = "gray"


        popup_html = f"""
        <div style="width:280px">

        <h4>{camera_name}</h4>

        <b>Camera Code:</b>
        {camera_code}
        <br><br>

        <b>City:</b>
        {city}
        <br>

        <b>Location:</b>
        {location}
        <br>

        <b>Status:</b>
        {status}
        <br>

        <b>Latitude:</b>
        {latitude}
        <br>

        <b>Longitude:</b>
        {longitude}

        </div>
        """


        folium.Marker(

            location=[
                latitude,
                longitude
            ],

            popup=folium.Popup(
                popup_html,
                max_width=350
            ),

            tooltip=(
                f"{camera_name} | "
                f"{status}"
            ),

            icon=folium.Icon(
                color=marker_color,
                icon="video-camera",
                prefix="fa"
            )

        ).add_to(
            marker_cluster
        )


st_folium(
    m,
    width=1200,
    height=600
)


# =========================================================
# CCTV RESOURCE INTEGRATION
# =========================================================

st.divider()

st.subheader(
    "CCTV Resource Integration"
)


resource_status = get_api_data(
    "/api/resources/status",
    show_error=False
)


if resource_status:

    available = resource_status.get(
        "available",
        False
    )

    status_code = resource_status.get(
        "status_code",
        "N/A"
    )

    resource_url = resource_status.get(
        "url",
        "N/A"
    )


    if available:

        st.success(
            "Resource Service: AVAILABLE"
        )

    else:

        st.warning(
            "Resource Service: UNAVAILABLE"
        )


    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "HTTP Status",
            status_code
        )

    with c2:

        st.metric(
            "Resource Access",
            (
                "Available"
                if available
                else
                "Unavailable"
            )
        )


    with st.expander(
        "Resource Service Details"
    ):

        st.write(
            "Service URL:"
        )

        st.code(
            str(resource_url)
        )

        st.json(
            resource_status
        )

else:

    st.info(
        "CCTV Resource Service status "
        "could not be retrieved."
    )


# =========================================================
# SYSTEM INFORMATION
# =========================================================

st.divider()

with st.expander(
    "System Information"
):

    st.write(
        "FastAPI Backend:",
        API_URL
    )

    st.write(
        "CCTV Demo Video:",
        str(VIDEO_PATH)
        if VIDEO_PATH
        else
        "Not found"
    )

    st.write(
        "AI Model:",
        str(MODEL_PATH)
        if MODEL_PATH
        else
        "Auto-generated Random Forest model"
    )

    st.write(
        "OpenCV:",
        cv2.__version__
    )

    st.write(
        "Total Cameras:",
        total_cameras
    )

    st.write(
        "Filtered Cameras:",
        len(filtered_df)
    )