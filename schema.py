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
    accel_x: float
    accel_y: float
    accel_z: float
    pitch: float
    roll: float
    yaw: float
    activity: str
