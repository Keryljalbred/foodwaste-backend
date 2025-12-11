import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

from app.ml.data_preparation import load_data_from_db, preprocess_data
from app.database import SessionLocal


BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "models", "waste_predictor.joblib")

os.makedirs(os.path.join(BASE_DIR, "models"), exist_ok=True)

# =====================================================
# 📌 1. Création du jeu d'entraînement depuis ta BASE SQL
# =====================================================
def create_training_dataset():
    print("📦 Chargement des données depuis PostgreSQL...")
    db = SessionLocal()
    df = load_data_from_db(db)
    df = preprocess_data(df)

    if df.empty:
        print("⚠️ Aucune donnée n'a été trouvée dans la base.")
        return None

    print(f"📊 {len(df)} lignes chargées depuis la DB")

    # -----------------------------------------------------
    # 🎯 Simulation du label (is_wasted)
    # -----------------------------------------------------
    df["is_wasted"] = df["status"].apply(
        lambda s: 1 if s in ["périmé", "bientôt périmé"] else 0
    )

    # -----------------------------------------------------
    # 🔥 Features UTILISÉES PAR TON API → IMPORTANT !
    # -----------------------------------------------------
    X = df[["quantity", "days_to_expire"]].fillna(0)
    y = df["is_wasted"]

    print("🧪 Jeu d'entraînement préparé.")
    return X, y


# =====================================================
# 📌 2. Entraînement du modèle de prédiction
# =====================================================
def train_model():
    dataset = create_training_dataset()
    if not dataset:
        print("❌ Aucun dataset disponible — arrêt.")
        return

    X, y = dataset

    # Séparation entraînement/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )

    print("🚀 Entraînement du modèle RandomForest...")

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=None,
        min_samples_split=2,
        random_state=42
    )

    model.fit(X_train, y_train)

    # Prédictions et évaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"✅ Modèle entraîné — Accuracy={acc:.3f}")
    print(classification_report(y_test, y_pred))

    # Sauvegarde du modèle
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"💾 Modèle sauvegardé dans {MODEL_PATH}")


# =====================================================
# 📌 3. Execution directe
# =====================================================
if __name__ == "__main__":
    print("🚀 Démarrage de l'entraînement du modèle FoodWaste Zero...")
    train_model()
    print("🏁 Entraînement terminé.")
