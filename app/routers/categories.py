from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from typing import List

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[dict])
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(models.Category).order_by(models.Category.name).all()
    return [{"id": c.id, "name": c.name} for c in categories]
