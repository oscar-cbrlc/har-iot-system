from fastapi import FastAPI, Depends, HTTPException, status, Security, WebSocket
from fastapi.security.api_key import APIKeyHeader
from preprocessing_transformers import FullPreprocessingTransformer

from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base

from schema import ReadingCreate, ReadingResponse, PredictionResponse
### #from scema import PredictionResponse
from models import SensorReading

import os
from dotenv import load_dotenv

from typing import List, Dict
import ydf
import joblib
import pandas as pd
import numpy as np

# web socket
class ConnectionManager:
    def __init__(self):
        # guardar conexiones activas: {device_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.active_connections[device_id] = websocket
    
    async def disconnect(self, device_id: str):
        if device_id in self.active_connections:
            del self.active_connections[device_id]
    
    async def send_prediction(self, message: dict, device_id:str):
        if device_id in self.active_connections:
            websocket = self.active_connections[device_id]
            await websocket.send_json(message)

manager = ConnectionManager()


# cargar las variables de entorno
load_dotenv('.env')

# crear las tablas de la base de datos si no existen
Base.metadata.create_all(bind=engine)

# determina si la api esta corriendo en el servidor o en un entorno local
is_production = os.getenv("ENVIRONMENT") == "production"

# define una dependencia para manejar la conexión a la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# crea la aplicación fastapi
app = FastAPI()

# leer la clave secreta desde variables de entorno
API_KEY = os.getenv("API_KEY")

# definir el nombre del header HTTP que deben usar los clientes
API_KEY_NAME = "X-API-Key"

# objeto para buscar en el header la api key
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# pipeline de preprocesamiento de datos
preprocessing_pipeline = joblib.load('preprocessing_pipeline.joblib')

model = ydf.load_model("har_rf_model")

activity_classes = model.label_classes() 



async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='invaliid api key'
    )

@app.post("/readings", response_model=ReadingResponse, dependencies=[Depends(get_api_key)])
async def create_reading(reading: ReadingCreate, db:Session = Depends(get_db)):
    # convertir de json a objeto
    db_reading = SensorReading(**reading.dict())

    # preparar insert a la bd
    db.add(db_reading)

    # ejecutar insert
    db.commit()

    # recuperar id  generados por la bd
    db.refresh(db_reading)

    # devuelve el objeto, automáticamente en json
    return db_reading

@app.post("/readings_batch", response_model=dict, dependencies=[Depends(get_api_key)])
async def create_reading_batch(readings: List[ReadingCreate], db:Session = Depends(get_db)):
    db_readings = []

    # para cada lectura
    for r in readings:
        # convertir de json a objeto
        db_reading = SensorReading(**r.dict())
         # preparar insert a la bd
        db.add(db_reading)
        # agregar a la lista el objeto
        db_readings.append(db_reading)
    # ejecutar transacción
    db.commit()

    # recuperar id generados por la bd
    for db_reading in db_readings:
        db.refresh(db_reading)

    # devuelve el número de inserciones
    return {'count': len(db_readings)}

# TODO GETs
@app.get("/readings", response_model=List[ReadingResponse], dependencies=[Depends(get_api_key)])
async def get_readings(limit=10000, device_id: str = None, db: Session = Depends(get_db)):

    #SELECT * FROM sensor_reading (WHERE device_id = device_id) ORDER BY id DESC LIMIT 10000
    query = db.query(SensorReading) 
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)
    return query.order_by(SensorReading.id.asc()).limit(limit).all()


@app.post("/predict_realtime", response_model=PredictionResponse)
async def predict_realtime(readings: List[ReadingCreate]):
    
    # convertir json a dataframe
    df_raw = pd.DataFrame([r.dict() for r in readings])

    current_device_id = df_raw.device_id
    
    # pasar por pipeline de preprocesamiento de los datos
    processed_features = preprocessing_pipeline.transform(df_raw)

    # predict and return
    prediction_probs = model.predict(processed_features)
    predicted_index = np.argmax(prediction_probs, axis=1)
    predicted_activity = activity_classes[predicted_index]
    return {
        device_id: current_device_id,
        accel_mean: processed_features['accel_mean'].iloc,
        accel_var: processed_features['accel_var'].iloc,
        gyro_mean: processed_features['gyro_mean'].iloc,
        gyro_var: processed_features['gyro_var'].iloc,
        accel_max: processed_features['accel_max'].iloc,
        accel_min: processed_features['accel_min'].iloc,
        gyro_max: processed_features['gyro_max'].iloc,
        gyro_min: processed_features['gyro_min'].iloc,
        activity: predicted_activity
    }
