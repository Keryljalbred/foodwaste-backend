from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://fwz:fwz_password@db:5433/foodwaste")
#DATABASE_URL = "postgresql+psycopg://fwz:fwz_password@localhost:5433/foodwaste"


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# 👇 Ajoute cette fonction ici
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
