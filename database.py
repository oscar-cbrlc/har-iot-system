from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:@localhost/postgres")
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "options": "-c timezone=America/Mexico_City"
    }
)
SessionLocal = sessionmaker(autocommit=False, bind=engine)
Base = declarative_base()