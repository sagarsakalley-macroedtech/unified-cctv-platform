import os
import requests


# =========================================================
# CCTV RESOURCE SERVICE
# =========================================================

RESOURCE_URL = os.getenv(
    "CCTV_RESOURCE_URL",
    "https://cctv.corp8.cloud/api/ingest"
)

REQUEST_TIMEOUT = 15


# =========================================================
# BASIC RESOURCE REQUEST
# =========================================================

def _request_resource():

    try:

        response = requests.get(
            RESOURCE_URL,
            timeout=REQUEST_TIMEOUT,
            headers={
                "Accept": "application/json",
                "User-Agent": "Unified-CCTV-Platform/1.0"
            },
            allow_redirects=True
        )

        content_type = response.headers.get(
            "content-type",
            ""
        ).lower()

        final_url = str(response.url)

        result = {
            "available": response.ok,
            "status_code": response.status_code,
            "url": RESOURCE_URL,
            "final_url": final_url,
            "content_type": content_type,
            "redirected": final_url != RESOURCE_URL
        }

        # =================================================
        # JSON RESPONSE
        # =================================================

        if "application/json" in content_type:

            try:

                result["data"] = response.json()

                result["response_type"] = "json"

                result["camera_data_available"] = True

            except ValueError:

                result["data"] = None

                result["response_type"] = "invalid_json"

                result["camera_data_available"] = False

                result["message"] = (
                    "Server declared JSON but returned invalid JSON."
                )

            return result


        # =================================================
        # HTML RESPONSE
        # =================================================

        if (
            "text/html" in content_type
            or response.text.lstrip().lower().startswith(
                "<!doctype html"
            )
            or response.text.lstrip().lower().startswith(
                "<html"
            )
        ):

            html_text = response.text[:5000]

            lower_html = html_text.lower()

            # ---------------------------------------------
            # Detect login page
            # ---------------------------------------------

            login_detected = any(
                keyword in lower_html
                for keyword in [
                    "login",
                    "sign in",
                    "signin",
                    "authentication",
                    "password",
                    "username"
                ]
            )

            result["data"] = None

            result["response_type"] = "html"

            result["camera_data_available"] = False

            result["authentication_required"] = login_detected

            if login_detected:

                result["message"] = (
                    "The CCTV resource endpoint is reachable, "
                    "but it returned an HTML login/authentication "
                    "page instead of camera data."
                )

            else:

                result["message"] = (
                    "The CCTV resource endpoint returned HTML "
                    "instead of camera data."
                )

            # Keep only a small diagnostic sample
            result["response_preview"] = html_text[:1000]

            return result


        # =================================================
        # OTHER RESPONSE
        # =================================================

        result["data"] = response.text[:5000]

        result["response_type"] = "other"

        result["camera_data_available"] = False

        result["message"] = (
            "Resource service responded, but the response "
            "was not JSON camera data."
        )

        return result


    # =====================================================
    # CONNECTION ERROR
    # =====================================================

    except requests.exceptions.Timeout:

        return {
            "available": False,
            "status_code": None,
            "url": RESOURCE_URL,
            "response_type": "timeout",
            "camera_data_available": False,
            "error": (
                "The CCTV resource service request timed out."
            )
        }


    except requests.exceptions.ConnectionError as e:

        return {
            "available": False,
            "status_code": None,
            "url": RESOURCE_URL,
            "response_type": "connection_error",
            "camera_data_available": False,
            "error": str(e)
        }


    except requests.exceptions.RequestException as e:

        return {
            "available": False,
            "status_code": None,
            "url": RESOURCE_URL,
            "response_type": "request_error",
            "camera_data_available": False,
            "error": str(e)
        }


# =========================================================
# RESOURCE STATUS
# =========================================================

def get_resource_status():

    result = _request_resource()

    return result


# =========================================================
# CAMERA CATALOGUE
# =========================================================

def get_camera_catalogue():

    result = _request_resource()

    # -----------------------------------------------------
    # RESOURCE NOT REACHABLE
    # -----------------------------------------------------

    if not result.get("available"):

        return {
            "available": False,
            "camera_data_available": False,
            "cameras": [],
            "count": 0,
            "message": (
                "CCTV resource service is unavailable."
            ),
            "details": result
        }


    # -----------------------------------------------------
    # HTML / LOGIN RESPONSE
    # -----------------------------------------------------

    if result.get("response_type") == "html":

        return {
            "available": True,
            "camera_data_available": False,
            "authentication_required": result.get(
                "authentication_required",
                False
            ),
            "cameras": [],
            "count": 0,
            "message": result.get(
                "message",
                "Resource returned HTML instead of camera data."
            ),
            "details": result
        }


    # -----------------------------------------------------
    # INVALID JSON
    # -----------------------------------------------------

    if result.get("response_type") == "invalid_json":

        return {
            "available": True,
            "camera_data_available": False,
            "cameras": [],
            "count": 0,
            "message": (
                "Resource service did not return valid JSON."
            ),
            "details": result
        }


    data = result.get("data")


    # =====================================================
    # CASE 1 — DIRECT LIST
    # =====================================================

    if isinstance(data, list):

        return {
            "available": True,
            "camera_data_available": True,
            "cameras": data,
            "count": len(data)
        }


    # =====================================================
    # CASE 2 — DICTIONARY
    # =====================================================

    if isinstance(data, dict):

        possible_keys = [
            "cameras",
            "camera",
            "resources",
            "data",
            "items",
            "camera_list",
            "camera_catalogue",
            "camera_catalog"
        ]


        for key in possible_keys:

            value = data.get(key)


            # ---------------------------------------------
            # Camera list
            # ---------------------------------------------

            if isinstance(value, list):

                return {
                    "available": True,
                    "camera_data_available": True,
                    "cameras": value,
                    "count": len(value),
                    "raw": data
                }


        # ---------------------------------------------
        # Sometimes data itself may contain one camera
        # ---------------------------------------------

        camera_indicators = [
            "camera_id",
            "camera_code",
            "camera_name",
            "camera",
            "stream_url",
            "rtsp_url"
        ]


        if any(
            key in data
            for key in camera_indicators
        ):

            return {
                "available": True,
                "camera_data_available": True,
                "cameras": [data],
                "count": 1,
                "raw": data
            }


        # ---------------------------------------------
        # JSON response but no camera catalogue
        # ---------------------------------------------

        return {
            "available": True,
            "camera_data_available": False,
            "cameras": [],
            "count": 0,
            "raw": data,
            "message": (
                "Resource service returned JSON successfully, "
                "but no camera catalogue was found."
            )
        }


    # =====================================================
    # UNKNOWN RESPONSE
    # =====================================================

    return {
        "available": True,
        "camera_data_available": False,
        "cameras": [],
        "count": 0,
        "raw": data,
        "message": (
            "Unknown CCTV resource response format."
        )
    }