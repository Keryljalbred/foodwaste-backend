import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.models import Product
from app.ml.model import model  # ⚠️ adapte le chemin si besoin


# ================================
# 1️⃣ Chargement des données (training)
# ================================
def load_data_from_db(db: Session):
    products = db.query(Product).all()
    if not products:
        return pd.DataFrame()

    data = [
        {
            "quantity": float(p.quantity),
            "expiration_date": p.expiration_date,
        }
        for p in products
    ]

    return pd.DataFrame(data)


# ================================
# 2️⃣ Préprocessing (training)
# ================================
def preprocess_data(df: pd.DataFrame):
    if df.empty:
        return df

    df["expiration_date"] = pd.to_datetime(df["expiration_date"], errors="coerce")
    df["days_to_expire"] = (df["expiration_date"] - datetime.now()).dt.days

    def get_status(days):
        if pd.isna(days):
            return 0          # inconnu
        elif days < 0:
            return 1          # périmé
        elif days <= 3:
            return 1          # bientôt périmé
        else:
            return 0          # frais

    df["target"] = df["days_to_expire"].apply(get_status)

    # 🔹 Colonnes utilisées par le modèle
    return df[["quantity", "days_to_expire", "target"]]


# ================================
# 3️⃣ PRÉDICTION (production)
# ================================
def get_prediction_and_message(product):
    """
    ⚠️ CETTE FONCTION MANQUAIT
    Elle est appelée par /products/predict
    """

    # 🔹 Calcul du nombre de jours restants
    if product.expiration_date:
        days_to_expire = (product.expiration_date - date.today()).days
    else:
        days_to_expire = 0

    # 🔹 DataFrame avec LES MÊMES FEATURES que l'entraînement
    X = pd.DataFrame([{
        "quantity": float(product.quantity),
        "days_to_expire": days_to_expire
    }])

    # 🔹 Prédiction ML
    prediction = model.predict(X)[0]

    # 🔹 Message métier
    if prediction == 1:
        message = "⚠️ Produit à risque de gaspillage"
    else:
        message = "✅ Produit encore consommable"

    return days_to_expire, int(prediction), message
