from fastapi import FastAPI, Depends, HTTPException
from fastapi_sqlalchemy import DBSessio
from sqlalchemy.orm import Session

from database import SessionLocal, engine

from schema import ReadingCreate, ReadingResponse
### #from scema import PredictionResponse
from models import SensorReading

import os
from dotenv import load_dotenv

from typing import List


load_dotenv('.env')

#create tables if they don't exist
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.post("/readings", response_model=ReadingResponse)
async def create_reading(reading: ReadingCreate, db:Session = Depends(get_db)):
    db_reading = SensorReading(**reading.dict())
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading) #for id and timestamp
    return db_reading

# TODO GETs
@app.get("/readings", response_model=List[ReadingResponse])
async def get_readings(limit=100, device_id: str = None, db: Session = Depends(db)):

    #SELECT * FROM sensor_reading (WHERE device_id = device_id) ORDER BY timestamp DESC LIMIT 100
    query = db.query(SensorReading) 
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)
    return query.order_by(SensorReading.timestamp.desc()).limit(limit).all
