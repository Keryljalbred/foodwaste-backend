# routes/barcode.py
import requests
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/barcode", tags=["Barcode"])

@router.get("/{code}")
def get_product_from_barcode(code: str):
    url = f"https://world.openfoodfacts.org/api/v0/product/{code}.json"
    res = requests.get(url)

    if res.status_code != 200:
        raise HTTPException(404, "Produit introuvable")

    data = res.json()

    if data.get("status") != 1:
        raise HTTPException(404, "Produit non trouvé dans OpenFoodFacts")

    product = data["product"]

    return {
        "barcode": code,
        "name": product.get("product_name"),
        "brand": product.get("brands"),
        "category": product.get("categories"),
        "image": product.get("image_front_url"),
    }
