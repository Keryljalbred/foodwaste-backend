import requests
from app.utils.translation import translate_text

BASE_URL = "https://world.openfoodfacts.org"

def get_product_info(query: str):
    """
    Récupère les informations produit depuis OpenFoodFacts.
    Si `query` est un code-barres → recherche directe
    Sinon → recherche par nom d’aliment (ex: yaourt)
    """
    # Vérifie si c’est un code-barres numérique
    if query.isdigit():
        url = f"{BASE_URL}/api/v0/product/{query}.json"
    else:
        url = f"{BASE_URL}/cgi/search.pl?search_terms={query}&search_simple=1&action=process&json=true"

    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Erreur de requête OpenFoodFacts"}

    data = response.json()

    # Cas 1 : recherche par code-barres
    if "product" in data:
        product = data.get("product")
    # Cas 2 : recherche par nom
    elif "products" in data and data["products"]:
        product = data["products"][0]
    else:
        return {"error": "Produit non trouvé"}

    return {
    "name": translate_text(product.get("product_name", "Inconnu")),
    "brand": product.get("brands", "Inconnue"),
    "nutriscore": product.get("nutriscore_grade", "Inconnu"),
    "ecoscore": product.get("ecoscore_grade", "Inconnu"),
    "ingredients": translate_text(product.get("ingredients_text", "Non spécifié"))
}
