from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from calendar import monthrange

from app.database import get_db
from ..security import get_current_user

from app.models import Product, ConsumptionHistory, User

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
def stats_overview(
    month: str | None = Query(
        None, description="Filtre mois au format YYYY-MM (ex: 2025-01)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les statistiques globales + tendances journalières optionnelles
    """

    # ==========================================================
    # 📆 GESTION DU FILTRE PAR MOIS
    # ==========================================================
    start_date = None
    end_date = None

    if month:
        try:
            year, m = map(int, month.split("-"))
            start_date = date(year, m, 1)
            end_date = date(year, m, monthrange(year, m)[1])
        except Exception:
            return {"error": "Format de mois invalide. Utilisez YYYY-MM"}

    # ==========================================================
    # 📦 PRODUITS DU FOYER
    # ==========================================================
    products_query = db.query(Product).filter(
        Product.user_id == current_user.id
    )

    if start_date:
        products_query = products_query.filter(
            Product.created_at >= start_date,
            Product.created_at <= end_date,
        )

    products = products_query.all()
    total_products = len(products)

    # ==========================================================
    # 🟢 CONSOMMÉS
    # ==========================================================
    consumed_query = db.query(ConsumptionHistory).filter(
        ConsumptionHistory.user_id == current_user.id,
        ConsumptionHistory.action == "consumed",
    )

    if start_date:
        consumed_query = consumed_query.filter(
            ConsumptionHistory.created_at >= start_date,
            ConsumptionHistory.created_at <= end_date,
        )

    consumed = consumed_query.count()

    # ==========================================================
    # 🔴 GASPILLÉS
    # ==========================================================
    wasted_query = db.query(ConsumptionHistory).filter(
        ConsumptionHistory.user_id == current_user.id,
        ConsumptionHistory.action == "wasted",
    )

    if start_date:
        wasted_query = wasted_query.filter(
            ConsumptionHistory.created_at >= start_date,
            ConsumptionHistory.created_at <= end_date,
        )

    wasted = wasted_query.count()

    # ==========================================================
    # ⏰ EXPIRÉS
    # ==========================================================
    expired = len(
        [
            p
            for p in products
            if p.expiration_date and p.expiration_date < date.today()
        ]
    )

    # ==========================================================
    # 📊 TAUX DE GASPILLAGE
    # ==========================================================
    waste_rate = (wasted / total_products * 100) if total_products else 0

    # ==========================================================
    # 📈 TENDANCES JOURNALIÈRES (OPTIONNEL)
    # ==========================================================
    daily_trend = []

    if start_date:
        history = (
            db.query(ConsumptionHistory)
            .filter(
                ConsumptionHistory.user_id == current_user.id,
                ConsumptionHistory.created_at >= start_date,
                ConsumptionHistory.created_at <= end_date,
            )
            .all()
        )

        trend_map = {}

        for h in history:
            day = h.created_at.date().isoformat()

            if day not in trend_map:
                trend_map[day] = {"day": day, "consumed": 0, "wasted": 0}

            if h.action == "consumed":
                trend_map[day]["consumed"] += 1
            elif h.action == "wasted":
                trend_map[day]["wasted"] += 1

        # Tri chronologique
        daily_trend = sorted(trend_map.values(), key=lambda x: x["day"])

    # ==========================================================
    # 🚀 RÉPONSE FINALE
    # ==========================================================
    return {
        "total": total_products,
        "consumed": consumed,
        "wasted": wasted,
        "expired": expired,
        "waste_rate": round(waste_rate, 2),
        "daily_trend": daily_trend,
    }
