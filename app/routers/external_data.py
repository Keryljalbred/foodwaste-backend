import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.models import Product
from app.database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/external-data", tags=["external"])

# ============================
# 🌍 Traduction FR → EN
# ============================
TRANSLATION_MAP = {
    # --- Produits de base ---
    "riz": "rice",
    "pâtes": "pasta",
    "pate": "pasta",
    "semoule": "semolina",
    "blé": "wheat",
    "haricot": "bean",
    "lentilles": "lentils",
    "pois chiches": "chickpeas",
    "quinoa": "quinoa",
    "épeautre": "spelt",

    # --- Fruits ---
    "pomme": "apple",
    "banane": "banana",
    "orange": "orange",
    "citron": "lemon",
    "fraise": "strawberry",
    "framboise": "raspberry",
    "mangue": "mango",
    "ananas": "pineapple",
    "kiwi": "kiwi",
    "raisin": "grape",
    "melon": "melon",
    "pastèque": "watermelon",
    "poire": "pear",
    "pêche": "peach",
    "abricot": "apricot",
    "prune": "plum",
    "cerise": "cherry",
    "grenade": "pomegranate",
    "papaye": "papaya",
    "myrtille": "blueberry",
    "cassis": "blackcurrant",

    # --- Légumes ---
    "carotte": "carrot",
    "tomate": "tomato",
    "pomme de terre": "potato",
    "patate douce": "sweet potato",
    "concombre": "cucumber",
    "courgette": "zucchini",
    "aubergine": "eggplant",
    "oignon": "onion",
    "échalote": "shallot",
    "ail": "garlic",
    "poivron": "bell pepper",
    "chou": "cabbage",
    "chou-fleur": "cauliflower",
    "brocoli": "broccoli",
    "épinard": "spinach",
    "salade": "lettuce",
    "haricot vert": "green beans",
    "petits pois": "peas",
    "poireau": "leek",
    "navet": "turnip",
    "betterave": "beetroot",
    "champignon": "mushroom",
    "céleri": "celery",
    "fenouil": "fennel",

    # --- Viandes ---
    "poulet": "chicken",
    "dinde": "turkey",
    "canard": "duck",
    "bœuf": "beef",
    "boeuf": "beef",
    "veau": "veal",
    "agneau": "lamb",
    "porc": "pork",
    "jambon": "ham",
    "saucisse": "sausage",
    "steak": "steak",
    "lardon": "bacon",

    # --- Poissons et fruits de mer ---
    "poisson": "fish",
    "saumon": "salmon",
    "thon": "tuna",
    "cabillaud": "cod",
    "merlan": "whiting",
    "maquereau": "mackerel",
    "crevette": "shrimp",
    "moule": "mussels",
    "calamar": "squid",
    "crabe": "crab",
    "homard": "lobster",

    # --- Produits laitiers ---
    "lait": "milk",
    "yaourt": "yogurt",
    "fromage": "cheese",
    "beurre": "butter",
    "crème": "cream",
    "crème fraîche": "fresh cream",
    "mozzarella": "mozzarella",
    "parmesan": "parmesan",

    # --- Boulangerie ---
    "pain": "bread",
    "baguette": "baguette",
    "brioche": "brioche",
    "croissant": "croissant",
    "viennoiserie": "pastry",

    # --- Épicerie ---
    "huile": "oil",
    "sel": "salt",
    "sucre": "sugar",
    "farine": "flour",
    "épice": "spice",
    "paprika": "paprika",
    "curry": "curry",
    "cumin": "cumin",
    "poivre": "pepper",
    "miel": "honey",
    "confiture": "jam",
    "chocolat": "chocolate",
    "cacao": "cocoa",
    "sirop": "syrup",

    # --- Boissons ---
    "eau": "water",
    "jus": "juice",
    "soda": "soda",
    "limonade": "lemonade",
    "café": "coffee",
    "the": "tea",
    "thé": "tea",

    # --- Œufs et dérivés ---
    "œuf": "egg",
    "oeuf": "egg",
    "omelette": "omelette",

    # --- Sauces ---
    "ketchup": "ketchup",
    "mayonnaise": "mayonnaise",
    "moutarde": "mustard",
    "sauce soja": "soy sauce",
    "sauce tomate": "tomato sauce",
    "pesto": "pesto",

    # --- Surgelés ---
    "frites": "fries",
    "glace": "ice cream",

    # --- Produits préparés ---
    "pizza": "pizza",
    "quiche": "quiche",
    "soupe": "soup",
    "bouillon": "broth",
    "salade": "salad",
}

def translate_to_english(text: str) -> str:
    """Traduit un texte FR -> EN via LibreTranslate."""
    if not text:
        return text

    try:
        r = requests.post(
            "https://libretranslate.de/translate",
            json={
                "q": text,
                "source": "fr",
                "target": "en",
                "format": "text"
            },
            timeout=5
        )
        return r.json().get("translatedText", text)
    except:
        return text


def normalize_name(name: str) -> str:
    name = name.lower().strip()
    return TRANSLATION_MAP.get(name, name)  # Si pas dans le dictionnaire → on garde le nom brut

# ============================
# 🥗 Nutriscore (OpenFoodFacts)
# ============================
def get_nutriscore(product_name: str):
    try:
        params = {
            "search_terms": product_name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
        }
        r = requests.get(
            "https://world.openfoodfacts.org/cgi/search.pl",
            params=params,
            timeout=6,
        ).json()

        products = r.get("products", [])
        if not products:
            return None

        p = products[0]

        return {
            "product_name": p.get("product_name", product_name),
            "nutriscore_grade": p.get("nutriscore_grade", "unknown"),
            "nutriscore_score": p.get("nutriscore_score"),
            "image": p.get("image_front_small_url"),
        }

    except:
        return None


# ============================
# 🍽 API recettes (TheMealDB)
# ============================
def get_recipes(product_name: str):
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={product_name}"
        meals = requests.get(url, timeout=6).json().get("meals")

        if not meals:
            return []

        recipes = []
        for m in meals:  # 👉 ICI : PAS DE LIMITE
            recipes.append({
                "id": m["idMeal"],
                "title": m["strMeal"],
                "thumbnail": m["strMealThumb"],
                "link": f"https://www.themealdb.com/meal/{m['idMeal']}",
            })

        return recipes

    except:
        return []


# ============================
# 🔥 Route principale
# ============================
@router.get("/{product_id}")
def external_data(
    product_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user.id
    ).first()

    if not product:
        raise HTTPException(404, "Produit introuvable")

    raw_name = product.name
    search_name = normalize_name(raw_name)

    print("🔍 Nom brut:", raw_name, "// Nom recherché:", search_name)

    # Nutriscore → basé sur search_name
    nutri = get_nutriscore(search_name)

    # Recettes → basé sur search_name
    recipes = get_recipes(search_name)

    return {
        "product_id": str(product.id),
        "product_name": search_name,
        "nutriscore": nutri,
        "recipes": recipes
    }
