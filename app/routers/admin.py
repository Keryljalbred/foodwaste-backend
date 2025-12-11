from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..security import get_current_user
from .. import models
from sqlalchemy import func

router = APIRouter(prefix="/admin", tags=["Administration"])

@router.get("/users")
def get_all_users(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Renvoie la liste de tous les utilisateurs avec :
    - nombre de produits
    - consommés
    - gaspillés
    """

    users = db.query(models.User).all()
    results = []

    for u in users:

        # Nombre total de produits
        product_count = (
            db.query(models.Product)
            .filter(models.Product.user_id == u.id)
            .count()
        )

        # Consommé
        consumed = (
            db.query(models.ConsumptionHistory)
            .filter(models.ConsumptionHistory.user_id == u.id, 
                    models.ConsumptionHistory.action == "consumed")
            .count()
        )

        # Gaspillé
        wasted = (
            db.query(models.ConsumptionHistory)
            .filter(models.ConsumptionHistory.user_id == u.id, 
                    models.ConsumptionHistory.action == "wasted")
            .count()
        )

        # Taux gaspillage
        rate = (wasted / (consumed + wasted) * 100) if (consumed + wasted) > 0 else 0

        results.append({
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "household_size": u.household_size,
            "product_count": product_count,
            "consumed": consumed,
            "wasted": wasted,
            "waste_rate": round(rate, 1),
            "created_at": u.created_at
        })

    return results
