from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# receiving data from ESP32, defines valid Json
class ReadingCreate(BaseModel):
    device_id: str
    timestamp: datetime
    accel_x: float
    accel_y: float
    accel_z: float
    pitch: float
    roll: float
    yaw: float
    activity: Optional[str] = None

# sending data
class ReadingResponse(ReadingCreate):
    id: int
    #

    class Config:
        orm_mode = True

# cuando est'e el modelo
class PredictionResponse(BaseModel):
    device_id: str
    accel_mean: float
    accel_var: float
    gyro_mean: float
    gyro_var: float
    accel_max: float
    accel_min: float
    gyro_max: float
    gyro_min: float
    activity: str
