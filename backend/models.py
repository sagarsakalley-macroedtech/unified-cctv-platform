from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from .db import Base


class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True)
    department_code = Column(String)
    department_name = Column(String)
    description = Column(String)
    status = Column(String)

    vms_systems = relationship(
        "VMSSystem",
        back_populates="department"
    )


class VMSSystem(Base):
    __tablename__ = "vms_systems"

    vms_id = Column(Integer, primary_key=True)
    vms_code = Column(String)
    department_id = Column(
        Integer,
        ForeignKey("departments.department_id")
    )
    vendor = Column(String)
    protocol = Column(String)
    host = Column(String)
    port = Column(Integer)
    status = Column(String)

    department = relationship(
        "Department",
        back_populates="vms_systems"
    )


class Camera(Base):
    __tablename__ = "cameras"

    camera_id = Column(Integer, primary_key=True)
    camera_code = Column(String)
    vms_id = Column(
        Integer,
        ForeignKey("vms_systems.vms_id")
    )
    camera_name = Column(String)
    location = Column(String)
    city = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    protocol = Column(String)
    stream_url = Column(String)
    status = Column(String)


class CameraHealth(Base):
    __tablename__ = "camera_health"

    health_id = Column(Integer, primary_key=True)
    camera_id = Column(
        Integer,
        ForeignKey("cameras.camera_id")
    )
    status = Column(String)
    fps = Column(Float)
    latency_ms = Column(Float)