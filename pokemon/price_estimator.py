import re

# Base de prix de référence (à enrichir progressivement)
REFERENCE_PRICES = {
    "gengar": 80,
    "charizard vmax": 280,
    "pikachu vmax": 140,
    "pikachu": 100,
    "arcanine": 260,
    "pyroli v": 45,
    "ninetales": 220,
    "gravalanch reverse": 30,
    "mega lopunny & jigglypuff gx": 110,
}

GRADE_MULTIPLIER = {
    10: 1.00,
    9.5: 0.90,
    9: 0.80,
    8.5: 0.70,
    8: 0.60,
    7.5: 0.50,
    7: 0.45,
}


def normalize_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"psa\\s*\\d+(?:\\.\\d+)?", "", name)
    name = re.sub(r"pca\\s*\\d+(?:\\.\\d+)?", "", name)
    name = re.sub(r"ccc\\s*\\d+(?:\\.\\d+)?", "", name)
    name = re.sub(r"collect aura\\s*\\d+(?:\\.\\d+)?", "", name)
    name = re.sub(r"pokemon|français|gradation", "", name)
    name = re.sub(r"\\s+", " ", name).strip()
    return name


def estimate_price(card_name, grader, grade):
    name = normalize_name(card_name)

    # Recherche de la meilleure correspondance
    for key, base_price in REFERENCE_PRICES.items():
        if key in name:
            multiplier = GRADE_MULTIPLIER.get(grade, 0.75)
            return round(base_price * multiplier, 2)

    return None