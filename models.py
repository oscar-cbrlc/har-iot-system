from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from database import Base

class SensorReading(Base):
    __tablename__ = 'sensor_reading';
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    timestamp = Column(DateTime, default = datetime.utcnow)
    accel_x = Column(Float)
    accel_y = Column(Float)
    accel_z = Column(Float)
    pitch = Column(Float)
    roll = Column(Float)
    yaw = Column(Float)
    activity = Column(String)