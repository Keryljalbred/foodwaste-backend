import requests

def translate_text(text: str, source_lang="en", target_lang="fr"):
    """
    Traduit un texte via l'API LibreTranslate.
    """
    if not text:
        return ""
    try:
        response = requests.post(
            "https://libretranslate.com/translate",
            data={
                "q": text,
                "source": source_lang,
                "target": target_lang,
                "format": "text"
            }
        )
        if response.status_code == 200:
            return response.json().get("translatedText", text)
        return text
    except Exception:
        return text
def translate_product_info(product_info: dict):
    """
    Traduit les champs pertinents des informations produit en français.
    """
    translated_info = product_info.copy()
    for field in ["name", "brand", "ingredients"]:
        if field in product_info:
            translated_info[field] = translate_text(product_info[field], source_lang="en", target_lang="fr")
    return translated_info