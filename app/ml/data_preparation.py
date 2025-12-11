import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Product

def load_data_from_db(db: Session):
    products = db.query(Product).all()
    if not products:
        return pd.DataFrame()

    data = [
        {
            "id": p.id,
            "name": p.name,
            "quantity": float(p.quantity),
            "expiration_date": p.expiration_date,
            "user_id": p.user_id,
        }
        for p in products
    ]
    return pd.DataFrame(data)


def preprocess_data(df: pd.DataFrame):
    if df.empty:
        return df

    df["expiration_date"] = pd.to_datetime(df["expiration_date"], errors="coerce")
    df["days_to_expire"] = (df["expiration_date"] - datetime.now()).dt.days

    def get_status(days):
        if pd.isna(days):
            return "inconnu"
        elif days < 0:
            return "périmé"
        elif days <= 3:
            return "bientôt périmé"
        else:
            return "frais"

    df["status"] = df["days_to_expire"].apply(get_status)

    return df
