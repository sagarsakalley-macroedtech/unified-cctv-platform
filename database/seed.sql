-- =========================================================
-- UNIFIED CCTV PLATFORM
-- SYNTHETIC SEED DATA
-- =========================================================

-- 1. DEPARTMENTS

INSERT INTO departments
(department_code, department_name, description, status)
VALUES
('POLICE', 'Police Department',
 'Police surveillance and security monitoring system', 'ACTIVE'),
('TRAFFIC', 'Traffic Department',
 'Traffic monitoring and road surveillance system', 'ACTIVE'),
('MUNICIPAL', 'Municipal Corporation',
 'Municipal infrastructure and public-area CCTV system', 'ACTIVE'),
('TRANSPORT', 'Transport Department',
 'Transport and mobility monitoring system', 'ACTIVE')
ON CONFLICT (department_code) DO NOTHING;


-- 2. VMS SYSTEMS

INSERT INTO vms_systems
(vms_code, department_id, vendor, protocol, host, port, status)
SELECT
'VMS-POLICE-01',
department_id,
'Demo VMS A',
'RTSP',
'127.0.0.1',
8554,
'ONLINE'
FROM departments
WHERE department_code = 'POLICE'
ON CONFLICT (vms_code) DO NOTHING;


INSERT INTO vms_systems
(vms_code, department_id, vendor, protocol, host, port, status)
SELECT
'VMS-TRAFFIC-01',
department_id,
'Demo VMS B',
'RTSP',
'127.0.0.1',
8555,
'ONLINE'
FROM departments
WHERE department_code = 'TRAFFIC'
ON CONFLICT (vms_code) DO NOTHING;


INSERT INTO vms_systems
(vms_code, department_id, vendor, protocol, host, port, status)
SELECT
'VMS-MUNICIPAL-01',
department_id,
'Demo VMS C',
'ONVIF',
'127.0.0.1',
8556,
'ONLINE'
FROM departments
WHERE department_code = 'MUNICIPAL'
ON CONFLICT (vms_code) DO NOTHING;


INSERT INTO vms_systems
(vms_code, department_id, vendor, protocol, host, port, status)
SELECT
'VMS-TRANSPORT-01',
department_id,
'Demo VMS D',
'API',
'127.0.0.1',
8557,
'ONLINE'
FROM departments
WHERE department_code = 'TRANSPORT'
ON CONFLICT (vms_code) DO NOTHING;


-- 3. POLICE CAMERAS - 15

INSERT INTO cameras
(camera_code, vms_id, camera_name, location, city,
 latitude, longitude, protocol, stream_url, status)
SELECT
'POL-CAM-' || LPAD(gs::TEXT, 3, '0'),
v.vms_id,
'Police Camera ' || LPAD(gs::TEXT, 3, '0'),
'Police Surveillance Zone ' || gs,
'Ahmedabad',
23.0225 + (gs * 0.001),
72.5714 + (gs * 0.001),
'RTSP',
'rtsp://127.0.0.1:8554/police' || gs,
CASE WHEN gs % 7 = 0 THEN 'OFFLINE' ELSE 'ONLINE' END
FROM generate_series(1,15) gs
CROSS JOIN vms_systems v
WHERE v.vms_code = 'VMS-POLICE-01'
ON CONFLICT (camera_code) DO NOTHING;


-- 4. TRAFFIC CAMERAS - 15

INSERT INTO cameras
(camera_code, vms_id, camera_name, location, city,
 latitude, longitude, protocol, stream_url, status)
SELECT
'TRF-CAM-' || LPAD(gs::TEXT, 3, '0'),
v.vms_id,
'Traffic Camera ' || LPAD(gs::TEXT, 3, '0'),
'Traffic Junction ' || gs,
'Surat',
21.1702 + (gs * 0.001),
72.8311 + (gs * 0.001),
'RTSP',
'rtsp://127.0.0.1:8555/traffic' || gs,
CASE WHEN gs % 8 = 0 THEN 'OFFLINE' ELSE 'ONLINE' END
FROM generate_series(1,15) gs
CROSS JOIN vms_systems v
WHERE v.vms_code = 'VMS-TRAFFIC-01'
ON CONFLICT (camera_code) DO NOTHING;


-- 5. MUNICIPAL CAMERAS - 10

INSERT INTO cameras
(camera_code, vms_id, camera_name, location, city,
 latitude, longitude, protocol, stream_url, status)
SELECT
'MUN-CAM-' || LPAD(gs::TEXT, 3, '0'),
v.vms_id,
'Municipal Camera ' || LPAD(gs::TEXT, 3, '0'),
'Municipal Zone ' || gs,
'Vadodara',
22.3072 + (gs * 0.001),
73.1812 + (gs * 0.001),
'ONVIF',
'rtsp://127.0.0.1:8556/municipal' || gs,
CASE WHEN gs % 9 = 0 THEN 'OFFLINE' ELSE 'ONLINE' END
FROM generate_series(1,10) gs
CROSS JOIN vms_systems v
WHERE v.vms_code = 'VMS-MUNICIPAL-01'
ON CONFLICT (camera_code) DO NOTHING;


-- 6. TRANSPORT CAMERAS - 10

INSERT INTO cameras
(camera_code, vms_id, camera_name, location, city,
 latitude, longitude, protocol, stream_url, status)
SELECT
'TRN-CAM-' || LPAD(gs::TEXT, 3, '0'),
v.vms_id,
'Transport Camera ' || LPAD(gs::TEXT, 3, '0'),
'Transport Zone ' || gs,
'Rajkot',
22.3039 + (gs * 0.001),
70.8022 + (gs * 0.001),
'API',
'rtsp://127.0.0.1:8557/transport' || gs,
CASE WHEN gs % 10 = 0 THEN 'OFFLINE' ELSE 'ONLINE' END
FROM generate_series(1,10) gs
CROSS JOIN vms_systems v
WHERE v.vms_code = 'VMS-TRANSPORT-01'
ON CONFLICT (camera_code) DO NOTHING;


-- 7. CAMERA HEALTH

INSERT INTO camera_health
(camera_id, status, fps, latency_ms)
SELECT
camera_id,
status,
CASE WHEN status = 'ONLINE' THEN 24.0 ELSE 0.0 END,
CASE WHEN status = 'ONLINE'
     THEN 120.0 + (camera_id % 80)
     ELSE 0.0
END
FROM cameras
WHERE NOT EXISTS (
    SELECT 1
    FROM camera_health ch
    WHERE ch.camera_id = cameras.camera_id
);