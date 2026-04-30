from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader

from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base

from schema import ReadingCreate, ReadingResponse
### #from scema import PredictionResponse
from models import SensorReading

import os
from dotenv import load_dotenv

from typing import List


load_dotenv('.env')

#create tables if they don't exist
Base.metadata.create_all(bind=engine)

is_production = os.getenv("ENVIRONMENT") == "production"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='invaliid api key'
    )

@app.post("/readings", response_model=ReadingResponse, dependencies=[Depends(get_api_key)])
async def create_reading(reading: ReadingCreate, db:Session = Depends(get_db)):
    db_reading = SensorReading(**reading.dict())
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading) #for id and timestamp
    return db_reading

@app.post("/readings_batch", response_model=dict, dependencies=[Depends(get_api_key)])
async def create_reading_batch(readings: List[ReadingCreate], db:Session = Depends(get_db)):
    db_readings = []
    for r in readings:
        db_reading = SensorReading(**r.dict())
        db.add(db_reading)
        db_readings.append(db_reading)
    db.commit()

    return {'count': len(db_readings)}

# TODO GETs
@app.get("/readings", response_model=List[ReadingResponse])
async def get_readings(limit=100, device_id: str = None, db: Session = Depends(get_db)):

    #SELECT * FROM sensor_reading (WHERE device_id = device_id) ORDER BY timestamp DESC LIMIT 100
    query = db.query(SensorReading) 
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)
    return query.order_by(SensorReading.timestamp.desc()).limit(limit).all()
