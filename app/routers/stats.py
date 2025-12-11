from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models import Product, ConsumptionHistory
from ..security import get_current_user

router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.get("/overview")
def stats_overview(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    
    # Tous les produits du foyer
    products = db.query(Product).filter(Product.user_id == current_user.id).all()
    total_products = len(products)

    # Consommés
    consumed = db.query(ConsumptionHistory).filter(
        ConsumptionHistory.user_id == current_user.id,
        ConsumptionHistory.action == "consumed"
    ).count()

    # Gaspillés
    wasted = db.query(ConsumptionHistory).filter(
        ConsumptionHistory.user_id == current_user.id,
        ConsumptionHistory.action == "wasted"
    ).count()

    # Expirés (non consommés + expiration date passée)
    expired = len([p for p in products if p.expiration_date and p.expiration_date < date.today()])

    waste_rate = (wasted / total_products * 100) if total_products else 0

    return {
        "total": total_products,
        "consumed": consumed,
        "wasted": wasted,
        "expired": expired,
        "waste_rate": round(waste_rate, 2)
    }
