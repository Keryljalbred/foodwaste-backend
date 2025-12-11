import requests

TRANSLATE_URL = "https://libretranslate.de/translate"
BASE_URL = "https://www.themealdb.com/api/json/v1/1/filter.php"
DETAIL_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php"


def translate_to_english(text: str) -> str:
    """Traduit un texte français en anglais (pour requêtes TheMealDB)."""
    try:
        payload = {"q": text, "source": "fr", "target": "en", "format": "text"}
        response = requests.post(TRANSLATE_URL, data=payload, timeout=5)
        if response.status_code == 200:
            return response.json().get("translatedText", text)
        return text
    except Exception:
        return text


def translate_to_french(text: str) -> str:
    """Traduit un texte anglais en français (pour affichage)."""
    try:
        payload = {"q": text, "source": "en", "target": "fr", "format": "text"}
        response = requests.post(TRANSLATE_URL, data=payload, timeout=5)
        if response.status_code == 200:
            return response.json().get("translatedText", text)
        return text
    except Exception:
        return text


def get_recipes_by_ingredient(ingredient: str):
    """
    Récupère des recettes à partir d’un ingrédient (FR ou EN).
    Traduction automatique des titres en français.
    """
    try:
        ingredient_en = translate_to_english(ingredient)
        response = requests.get(BASE_URL, params={"i": ingredient_en}, timeout=5)
        if response.status_code != 200:
            return []

        data = response.json()
        meals = data.get("meals") or []
        recipes = []

        for meal in meals:
            name_en = meal.get("strMeal")
            name_fr = translate_to_french(name_en)
            recipes.append({
                "name": name_fr,
                "thumbnail": meal.get("strMealThumb"),
                "id": meal.get("idMeal")
            })

        return recipes

    except Exception as e:
        print(f"❌ Erreur get_recipes_by_ingredient : {e}")
        return []


def get_recipe_details(recipe_id: str):
    """
    Récupère les détails complets d’une recette à partir de son ID (TheMealDB).
    """
    try:
        response = requests.get(DETAIL_URL, params={"i": recipe_id}, timeout=5)
        if response.status_code != 200:
            return {"error": "Erreur API TheMealDB"}

        data = response.json()
        meals = data.get("meals")
        if not meals:
            return {"error": "Recette non trouvée"}

        meal = meals[0]
        return {
            "name": translate_to_french(meal.get("strMeal")),
            "category": translate_to_french(meal.get("strCategory")),
            "area": translate_to_french(meal.get("strArea")),
            "instructions": translate_to_french(meal.get("strInstructions", "Aucune instruction.")),
            "thumbnail": meal.get("strMealThumb"),
            "tags": meal.get("strTags"),
            "youtube": meal.get("strYoutube"),
            "ingredients": [
                {
                    "ingredient": translate_to_french(meal.get(f"strIngredient{i}")),
                    "measure": meal.get(f"strMeasure{i}")
                }
                for i in range(1, 21)
                if meal.get(f"strIngredient{i}")
            ]
        }
    except Exception as e:
        print(f"❌ Erreur get_recipe_details : {e}")
        return {"error": "Erreur interne lors de la récupération de la recette"}

