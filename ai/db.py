import os
import psycopg2


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "cctv_registry"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "PUne26@!"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_camera_health(camera_id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                uptime,
                response_time,
                packet_loss,
                cpu_usage
            FROM camera_health
            WHERE camera_id = %s
            ORDER BY prediction_time DESC
            LIMIT 1
            """,
            (camera_id,)
        )

        row = cursor.fetchone()

        cursor.close()

        return row

    finally:
        conn.close()