from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Cambiamos a una URL de SQLite. Esto creará un archivo llamado `karaoke.db` en la raíz del proyecto.
SQLALCHEMY_DATABASE_URL = "sqlite:///./karaoke.db"

# Para SQLite, es necesario añadir connect_args={"check_same_thread": False} para que funcione con FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()