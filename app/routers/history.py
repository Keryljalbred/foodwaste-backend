from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ConsumptionHistory, Product
from app.security import get_current_user

router = APIRouter(prefix="/history", tags=["Historique"])

@router.get("/")
def get_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    records = (
        db.query(ConsumptionHistory)
        .filter(ConsumptionHistory.user_id == current_user.id)
        .order_by(ConsumptionHistory.created_at.desc())
        .all()
    )

    results = []
    for r in records:
        product = db.query(Product).filter(Product.id == r.product_id).first()
        results.append({
            "id": str(r.id),
            "action": r.action,
            "amount": float(r.amount),
            "created_at": r.created_at,
            "product_name": product.name if product else "Produit supprimé"
        })

    return results
