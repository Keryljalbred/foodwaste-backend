import pandas as pd
import numpy as np
from datetime import date, timedelta
import random
import os

PRODUCTS = [
    "yaourt", "lait", "poulet", "riz", "pâtes", "fromage",
    "pommes", "bananes", "poisson", "tomates", "œufs",
    "beurre", "huile", "café", "céréales", "thon", "pain"
]

def generate_fake_dataset(n=500):
    rows = []

    for _ in range(n):
        name = random.choice(PRODUCTS)
        quantity = round(random.uniform(1, 10), 2)

        # Simuler expiration : passé, proche, futur
        choice = random.random()

        # 20% périmés
        if choice < 0.2:
            days_left = random.randint(-15, -1)
        # 30% bientôt périmés
        elif choice < 0.5:
            days_left = random.randint(0, 3)
        # 50% frais
        else:
            days_left = random.randint(4, 30)

        expiration_date = date.today() + timedelta(days=days_left)

        # Status
        if days_left < 0:
            status = "périmé"
        elif days_left <= 3:
            status = "bientôt périmé"
        else:
            status = "frais"

        # Label ML
        is_wasted = 1 if status in ["périmé", "bientôt périmé"] else 0

        rows.append({
            "name": name,
            "quantity": quantity,
            "expiration_date": expiration_date,
            "days_to_expire": days_left,
            "status": status,
            "is_wasted": is_wasted
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_fake_dataset(500)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/fake_products.csv", index=False)
    print("🎉 Dataset simulé généré : data/fake_products.csv")
    print(df.head())
