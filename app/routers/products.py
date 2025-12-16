# --- Imports nécessaires ---
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
import joblib
import os
import numpy as np
from uuid import UUID
from datetime import datetime, date
from ..schemas import ProductCreate, ProductOut
from .. import models
from typing import List
from ..security import get_current_user
from pydantic import BaseModel
from app.email_utils import send_email



class ProductAction(BaseModel):
    amount: float = 1.0


router = APIRouter(prefix="/products", tags=["Products"])


# ============================
# 🔥 Charger le modèle ML
# ============================
MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ml/models/waste_predictor.joblib"))


def load_ml_model():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return None
    return None


# ============================
# 🔮 Fonction de prédiction ML
# ============================
def get_prediction_and_message(product: models.Product):
    today = date.today()

    days_left = (product.expiration_date - today).days if product.expiration_date else None

    # ---- CAS 1 : périmé ----
    if days_left is not None and days_left < 0:
        return days_left, 2, "⚠️ Produit périmé"

    # ---- Charger modèle ----
    model = load_ml_model()
    prediction = None

    # ---- CAS 2 : prédiction ML ----
    if model and days_left is not None:
        try:
            X = np.array([[float(product.quantity), days_left]])
            prediction = int(model.predict(X)[0])
        except:
            prediction = None

    # ---- CAS 3 : risque ----
    # - modèle ML dit 1
    # - ou ≤ 3 jours restants
    if (prediction == 1) or (days_left is not None and days_left <= 3):
        return days_left, 1, "🔥 Produit à risque de gaspillage"

    # ---- CAS 4 : sûr ----
    return days_left, 0, "✅ Produit sûr"



# ============================
# ➕ Ajouter un produit
# ============================
@router.post("/", response_model=ProductOut)
def add_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.expiration_date:
        if payload.expiration_date < date.today():
            raise HTTPException(
                status_code=400,
                detail="La date de péremption ne peut pas être antérieure à aujourd’hui."
            )
    product = models.Product(
        name=payload.name,
        quantity=payload.quantity,
        expiration_date=payload.expiration_date,
        category_id=payload.category_id,
        user_id=current_user.id,
    )


    days_left, pred, msg = get_prediction_and_message(product)
    product.prediction = pred
    product.message = msg

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


# ============================
# 📋 Lister les produits
# ============================
@router.get("/", response_model=List[dict])
def list_products(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    
):
    products = (
        db.query(models.Product)
        .filter(models.Product.user_id == user.id)
        .order_by(
            models.Product.expiration_date.is_(None),
            models.Product.expiration_date,
        )
        .all()
    )

    enriched = []
    for p in products:
        days_left, pred, msg = get_prediction_and_message(p)

        enriched.append(
            {
                "id": str(p.id),
                "name": p.name,
                "quantity": float(p.quantity),
                "expiration_date": str(p.expiration_date) if p.expiration_date else None,
                "days_left": days_left,
                "prediction": pred,
                "message": msg,
                "category": p.category_rel.name if p.category_rel else None

            }
        )

    return enriched


# ============================
# 🗑️ Supprimer un produit
# ============================
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.user_id == current_user.id,
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    db.delete(product)
    db.commit()
    return None


# ============================
# 🔮 Prédiction directe
# ============================
class PredictRequest(BaseModel):
    product_id: str
@router.post("/predict")
def predict_product(
    payload: PredictRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Vérifier si le produit appartient à l'utilisateur
    product = db.query(Product).filter(
        Product.id == payload.product_id,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(404, "Produit introuvable")

    # ⬅️ Ici on appelle enfin ton modèle ML !
    days_left, pred, msg = get_prediction_and_message(product)

    return {
        "id": str(product.id),
        "name": product.name,
        "quantity": float(product.quantity),
        "expiration_date": str(product.expiration_date) if product.expiration_date else None,
        "days_left": days_left,
        "prediction": pred,
        "message": msg,
    }


# ============================
# 🍽️ Consommer un produit
# ============================
@router.post("/{product_id}/consume")
def consume_product(
    product_id: str,
    payload: ProductAction,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    p = (
        db.query(models.Product)
        .filter(models.Product.user_id == user.id, models.Product.id == product_id)
        .first()
    )

    if not p:
        raise HTTPException(404, "Produit introuvable")

    if payload.amount <= 0 or payload.amount > float(p.quantity):
        raise HTTPException(400, "Quantité invalide")

    p.quantity = float(p.quantity) - payload.amount

    # Historique
    db.add(
        models.ConsumptionHistory(
            user_id=user.id,
            product_id=p.id,
            action="consumed",
            amount=payload.amount,
        )
    )

    if p.quantity <= 0:
        db.delete(p)
        db.commit()
        return {"status": "deleted", "message": "Produit consommé"}

    db.commit()
    db.refresh(p)

    days_left, pred, msg = get_prediction_and_message(p)
    p.prediction = pred
    p.message = msg

    db.commit()
    db.refresh(p)

    return {
        "id": str(p.id),
        "name": p.name,
        "quantity": float(p.quantity),
        "expiration_date": str(p.expiration_date),
        "days_left": days_left,
        "prediction": pred,
        "message": msg,
    }


# ============================
# 🚮 Gaspillage
# ============================
@router.post("/{product_id}/waste")
def waste_product(
    product_id: str,
    payload: ProductAction,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    p = (
        db.query(models.Product)
        .filter(models.Product.user_id == user.id, models.Product.id == product_id)
        .first()
    )

    if not p:
        raise HTTPException(404, "Produit introuvable")

    if payload.amount <= 0 or payload.amount > float(p.quantity):
        raise HTTPException(400, "Quantité invalide")
    
    p.quantity = float(p.quantity) - payload.amount

    db.add(
        models.ConsumptionHistory(
            user_id=user.id,
            product_id=p.id,
            action="wasted",
            amount=payload.amount,
        )
    )

    if p.quantity <= 0:
        db.delete(p)
        db.commit()
        return {"status": "deleted", "message": "Produit gaspillé"}

    db.commit()
    db.refresh(p)

    days_left, pred, msg = get_prediction_and_message(p)
    p.prediction = pred
    p.message = msg

    db.commit()
    db.refresh(p)

    return {
        "id": str(p.id),
        "name": p.name,
        "quantity": float(p.quantity),
        "expiration_date": str(p.expiration_date),
        "days_left": days_left,
        "prediction": pred,
        "message": msg,
    }


# ============================
# 🚀 Rafraîchissement interne
# ============================
@router.post("/internal/refresh", tags=["internal"])
def internal_refresh_predictions(db: Session = Depends(get_db)):
    model = load_ml_model()
    today = date.today()

    products = db.query(models.Product).all()
    updated = 0

    for p in products:
        days_left = (
            (p.expiration_date - today).days
            if p.expiration_date else None
        )

        # Périmé
        if days_left is None:
            p.prediction = 0
            p.message = "✅ Produit sûr"

        elif days_left < 0:
            p.prediction = 2
            p.message = "⚠️ Produit périmé"

        elif model:
            try:
                X = np.array([[float(p.quantity), days_left]])
                pred = int(model.predict(X)[0])
                if pred == 1 or days_left <= 3:
                    p.prediction = 1
                    p.message = "🔥 Produit à risque de gaspillage"
                else:
                    p.prediction = 0
                    p.message = "✅ Produit sûr"
            except Exception:
                p.prediction = 0
                p.message = "✅ Produit sûr"

        else:
            if days_left <= 3:
                p.prediction = 1
                p.message = "🔥 Produit à risque"
            else:
                p.prediction = 0
                p.message = "✅ Produit sûr"

        updated += 1

    db.commit()
    return {"status": "ok", "updated": updated}


# ============================
# 📊 Stats journalières internes
# ============================
@router.post("/internal/stats", tags=["internal"])
def record_daily_stats(db: Session = Depends(get_db)):
    today = date.today()

    products = db.query(models.Product).all()

    expired = risky = safe = 0

    for p in products:
        if not p.expiration_date:
            safe += 1
            continue

        days_left = (p.expiration_date - today).days

        if days_left < 0:
            expired += 1
        elif days_left <= 3:
            risky += 1
        else:
            safe += 1

    total = len(products)

    existing = db.query(models.DailyStats).filter(
        models.DailyStats.stat_date == today
    ).first()

    if existing:
        existing.total_products = total
        existing.expired = expired
        existing.risky = risky
        existing.safe = safe
    else:
        db.add(
            models.DailyStats(
                stat_date=today,
                total_products=total,
                expired=expired,
                risky=risky,
                safe=safe,
            )
        )

    db.commit()

    return {
        "stat_date": today.isoformat(),
        "expired": expired,
        "risky": risky,
        "safe": safe,
        "total": total,
        "status": "ok",
    }

   # ⬅️ adapte l'import à ton projet


@router.post("/internal/send_alerts", tags=["internal"])
def send_risk_alerts(db: Session = Depends(get_db)):
    today = date.today()
    users = db.query(models.User).all()
    total_alerts_sent = 0

    for user in users:
        products = (
            db.query(models.Product)
            .filter(models.Product.user_id == user.id)
            .all()
        )

        risky = []
        for p in products:
            if not p.expiration_date:
                continue
            days_left = (p.expiration_date - today).days
            if p.prediction == 1 or days_left <= 3:
                risky.append(p)

        if not risky:
            continue

        # On choisit le premier produit pour proposer des recettes
        main_product = risky[0]

        # 🔵 Appel à ton API existante pour récupérer les recettes
        try:
            r = requests.get(
                f"http://api:8000/external-data/{main_product.id}",
                timeout=5
            )
            recipes = r.json().get("recipes", [])
        except:
            recipes = []

        # 🔵 Construire la liste des produits à risque
        product_list = "".join(
            f"<li><b>{p.name}</b> — reste {(p.expiration_date - today).days} jours</li>"
            for p in risky
        )

        # 🔵 Construire la liste HTML des recettes
        recipes_html = ""
        for rec in recipes[:3]:  # max 3 recettes pour éviter un email trop long
            recipes_html += f"""
                <li>
                    <b>{rec['title']}</b><br>
                    <img src="{rec.get('thumbnail','')}" width="180" style="border-radius:8px;margin-top:4px"><br>
                    <a href="{rec['link']}">Voir la recette</a>
                </li><br>
            """

        # 🔵 Bouton "consommer maintenant"
        consume_button = f"""
            <a href="https://foodwaste-zero.info"
               style="display:inline-block;padding:12px 20px;
               background:#05a66b;color:white;border-radius:8px;
               text-decoration:none;font-weight:bold">
               Consommer maintenant
            </a>
        """

        # 🔵 Contenu final email
        html_content = f"""
        <h2>⚠️ Alerte FoodWaste Zero</h2>
        <p>Des produits arrivent bientôt à expiration :</p>

        <p style="font-size:15px;margin-top:0">
              Bonne nouvelle 
              Vous pouvez encore <b>éviter le gaspillage</b> en agissant dès maintenant.
            </p>

            <p style="font-size:14px;margin-bottom:6px">
              <b>Produits concernés :</b>
            </p>

        <ul>{product_list}</ul>

       

        <h3> 👉 Gérer mes produits</h3>
        {consume_button}

        <p> Chaque produit sauvé fait la différence 🌍  
              Merci d’agir contre le gaspillage alimentaire.</p>
        """

        send_email(
            user.email,
            "⚠️ Produits alimentaires à risque",
            html_content
        )

        total_alerts_sent += 1

    return {"status": "ok", "emails_sent": total_alerts_sent}
