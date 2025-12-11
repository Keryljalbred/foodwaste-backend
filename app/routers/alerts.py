from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..security import get_current_user
from .. import models
from datetime import date

router = APIRouter(prefix="/alerts", tags=["Alertes"])

@router.get("/")
def get_alerts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Renvoie tous les produits proches de la date d'expiration :
    - days_left < 0  = périmé
    - days_left <= 2 = alerte
    """

    today = date.today()

    products = (
        db.query(models.Product)
        .filter(models.Product.user_id == current_user.id)
        .all()
    )

    results = []
    for p in products:
        if p.expiration_date:
            days_left = (p.expiration_date - today).days
        else:
            days_left = None

        if days_left is not None and days_left <= 2:
            results.append({
                "id": str(p.id),
                "name": p.name,
                "category": p.category,
                "days_left": days_left,
                "expiration_date": p.expiration_date,
                "message": p.message
            })

    # Trier : périmé d’abord
    results = sorted(results, key=lambda x: x["days_left"])

    return results
