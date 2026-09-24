-- =========================================================
-- UNIFIED CCTV PLATFORM
-- DATABASE SCHEMA
-- =========================================================

-- =========================================================
-- DEPARTMENTS
-- =========================================================

CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    department_code VARCHAR(50) UNIQUE NOT NULL,
    department_name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(30) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- VMS SYSTEMS
-- =========================================================

CREATE TABLE IF NOT EXISTS vms_systems (
    vms_id SERIAL PRIMARY KEY,

    vms_code VARCHAR(50) UNIQUE NOT NULL,

    department_id INTEGER NOT NULL,

    vendor VARCHAR(150),

    protocol VARCHAR(50),

    host VARCHAR(255),

    port INTEGER,

    status VARCHAR(30) DEFAULT 'ONLINE',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_vms_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
);


-- =========================================================
-- CAMERAS
-- =========================================================

CREATE TABLE IF NOT EXISTS cameras (
    camera_id SERIAL PRIMARY KEY,

    camera_code VARCHAR(50) UNIQUE NOT NULL,

    vms_id INTEGER NOT NULL,

    camera_name VARCHAR(200) NOT NULL,

    location VARCHAR(300),

    city VARCHAR(100),

    latitude DOUBLE PRECISION,

    longitude DOUBLE PRECISION,

    protocol VARCHAR(50),

    stream_url TEXT,

    status VARCHAR(30) DEFAULT 'OFFLINE',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_camera_vms
        FOREIGN KEY (vms_id)
        REFERENCES vms_systems(vms_id)
);


-- =========================================================
-- CAMERA HEALTH
-- =========================================================

CREATE TABLE IF NOT EXISTS camera_health (
    health_id SERIAL PRIMARY KEY,

    camera_id INTEGER NOT NULL,

    status VARCHAR(30),

    fps DOUBLE PRECISION,

    latency_ms DOUBLE PRECISION,

    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_health_camera
        FOREIGN KEY (camera_id)
        REFERENCES cameras(camera_id)
);


-- =========================================================
-- VEHICLE EVENTS
-- =========================================================

CREATE TABLE IF NOT EXISTS vehicle_events (
    event_id SERIAL PRIMARY KEY,

    camera_id INTEGER NOT NULL,

    event_time TIMESTAMP NOT NULL,

    vehicle_type VARCHAR(100),

    plate_number VARCHAR(50),

    confidence DOUBLE PRECISION,

    snapshot_path TEXT,

    event_type VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_event_camera
        FOREIGN KEY (camera_id)
        REFERENCES cameras(camera_id)
);


-- =========================================================
-- ALERTS
-- =========================================================

CREATE TABLE IF NOT EXISTS alerts (
    alert_id SERIAL PRIMARY KEY,

    event_id INTEGER,

    alert_type VARCHAR(100),

    severity VARCHAR(30),

    message TEXT,

    status VARCHAR(30) DEFAULT 'OPEN',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_alert_event
        FOREIGN KEY (event_id)
        REFERENCES vehicle_events(event_id)
);


-- =========================================================
-- INDEXES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_camera_status
ON cameras(status);

CREATE INDEX IF NOT EXISTS idx_camera_city
ON cameras(city);

CREATE INDEX IF NOT EXISTS idx_camera_vms
ON cameras(vms_id);

CREATE INDEX IF NOT EXISTS idx_vehicle_plate
ON vehicle_events(plate_number);

CREATE INDEX IF NOT EXISTS idx_vehicle_event_time
ON vehicle_events(event_time);

CREATE INDEX IF NOT EXISTS idx_alert_status
ON alerts(status);