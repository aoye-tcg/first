import time
import re
import requests
from bs4 import BeautifulSoup

from price_estimator import estimate_price
from telegram_alert import send_alert


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://gradedcardcenter.com"
FIXED_PRICE_URL = f"{BASE_URL}/filtres/fixed-price"

ALLOWED_GRADERS = {
    "PSA",
    "PCA",
    "COLLECT AURA",
    "CCC"
}

SEEN = set()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"
}


# ============================================================
# OUTILS
# ============================================================

def get_page(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        return response

    except Exception as e:
        print(
            f"❌ Erreur connexion {url} : {e}",
            flush=True
        )

        return None


def clean_text(text):
    return " ".join(text.split())


def detect_grader(text):
    text_upper = text.upper()

    if "COLLECT AURA" in text_upper:
        return "COLLECT AURA"

    if "PSA" in text_upper:
        return "PSA"

    if "PCA" in text_upper:
        return "PCA"

    if re.search(r"\bCCC\b", text_upper):
        return "CCC"

    return None


def extract_grade(text):
    match = re.search(
        r"\b(?:PSA|PCA|CCC)\s*(?:GRADE\s*)?(\d+(?:[.,]\d+)?)",
        text,
        re.IGNORECASE
    )

    if match:
        try:
            return float(
                match.group(1).replace(",", ".")
            )
        except ValueError:
            pass

    return None


def detect_price(text):
    patterns = [
        r"(\d+(?:[.,]\d{1,2})?)\s*€",
        r"€\s*(\d+(?:[.,]\d{1,2})?)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            try:
                return float(
                    match.group(1).replace(",", ".")
                )
            except ValueError:
                pass

    return None


# ============================================================
# EXTRACTION DU NOM DE LA CARTE
# ============================================================

def extract_card_name(text, grader, grade):
    """
    Essaie de récupérer uniquement le nom de la carte
    à partir du texte de l'annonce.

    Exemple :
    PSA 9 Arcanine Gradation ...

    devient :

    Arcanine
    """

    text = clean_text(text)

    # --------------------------------------------------------
    # 1. Cherche explicitement le bloc autour du grade
    # --------------------------------------------------------

    pattern = re.compile(
        rf"\b{re.escape(grader)}\s*"
        rf"{re.escape(str(grade).replace('.0', ''))}"
        rf"\s+(.+?)(?=\s+Gradation\b|\s+Pokemon\b|\s+Pokémon\b|\s+\d+\s*€|\s+Prix fixe\b)",
        re.IGNORECASE
    )

    match = pattern.search(text)

    if match:
        name = clean_text(match.group(1))

        if name:
            return name

    # --------------------------------------------------------
    # 2. Version plus permissive
    # --------------------------------------------------------

    pattern = re.compile(
        rf"\b{re.escape(grader)}\s*"
        rf"{re.escape(str(grade).replace('.0', ''))}"
        rf"\s+(.+?)(?=\s+Gradation\b|\s+Vends\b|\s+Accueil\b)",
        re.IGNORECASE
    )

    match = pattern.search(text)

    if match:
        name = clean_text(match.group(1))

        if name:
            return name

    # --------------------------------------------------------
    # 3. Dernier secours :
    # prend quelques mots après PSA/PCA + grade
    # --------------------------------------------------------

    pattern = re.compile(
        rf"\b{re.escape(grader)}\s*"
        rf"{re.escape(str(grade).replace('.0', ''))}\s+"
        rf"(.+)",
        re.IGNORECASE
    )

    match = pattern.search(text)

    if match:
        name = clean_text(match.group(1))

        # On coupe sur les éléments connus du site
        stop_words = [
            "Gradation",
            "Vends tes articles",
            "Français",
            "Accueil",
            "Enchères",
            "LIVE",
            "Achat à prix fixe",
            "Explorer",
            "À propos",
            "Nouveau : Bonnes affaires",
            "Pokemon",
            "Pokémon"
        ]

        for stop in stop_words:
            position = name.lower().find(stop.lower())

            if position > 0:
                name = name[:position].strip()

        if name:
            return name

    return None


# ============================================================
# ANALYSE D'UNE ANNONCE
# ============================================================

def analyse_listing(url):

    print(
        f"\n🎴 Analyse annonce : {url}",
        flush=True
    )

    response = get_page(url)

    if response is None:
        return

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    text = clean_text(
        soup.get_text(" ", strip=True)
    )

    # --------------------------------------------------------
    # GRADUEUR
    # --------------------------------------------------------

    grader = detect_grader(text)

    if not grader:
        print(
            "⏭️ Gradueur non autorisé ou introuvable",
            flush=True
        )
        return

    print(
        f"🏷️ Gradueur détecté : {grader}",
        flush=True
    )

    # --------------------------------------------------------
    # GRADE
    # --------------------------------------------------------

    grade = extract_grade(text)

    if grade is not None:
        print(
            f"📊 Grade : {grade}",
            flush=True
        )
    else:
        print(
            "📊 Grade : non détecté",
            flush=True
        )

    # --------------------------------------------------------
    # NOM DE CARTE
    # --------------------------------------------------------

    card_name = extract_card_name(
        text,
        grader,
        grade
    )

    if not card_name:

        print(
            "❌ Nom de carte impossible à extraire",
            flush=True
        )

        return

    print(
        f"🎴 Carte extraite : {card_name}",
        flush=True
    )

    # --------------------------------------------------------
    # PRIX
    # --------------------------------------------------------

    price = detect_price(text)

    if price is None:

        print(
            "💰 Prix non détecté",
            flush=True
        )

        return

    print(
        f"💰 Prix détecté : {price} €",
        flush=True
    )

    # --------------------------------------------------------
    # ESTIMATION
    # --------------------------------------------------------

    try:

        estimated = estimate_price(
            card_name,
            grader,
            grade
        )

    except Exception as e:

        print(
            f"⚠️ Erreur estimation : {e}",
            flush=True
        )

        estimated = None

    if estimated is None:

        print(
            "💰 Estimation indisponible",
            flush=True
        )

        return

    print(
        f"📈 Estimation : {estimated} €",
        flush=True
    )

    # --------------------------------------------------------
    # SEUIL BONNE AFFAIRE
    # --------------------------------------------------------

    threshold = estimated * 0.75

    print(
        f"🎯 Seuil bonne affaire : {threshold:.2f} €",
        flush=True
    )

    if price <= threshold:

        if url in SEEN:

            print(
                "⏭️ Annonce déjà signalée",
                flush=True
            )

            return

        SEEN.add(url)

        print(
            "🚨 BONNE AFFAIRE DÉTECTÉE !",
            flush=True
        )

        try:

            send_alert(
                card_name,
                price,
                estimated,
                url
            )

            print(
                "📲 Alerte Telegram envoyée !",
                flush=True
            )

        except Exception as e:

            print(
                f"❌ Erreur envoi Telegram : {e}",
                flush=True
            )

    else:

        print(
            "❌ Pas suffisamment sous-évaluée",
            flush=True
        )


# ============================================================
# RÉCUPÉRATION DES ANNONCES À PRIX FIXE
        if "/item/" not in href:
            continue

        if href.startswith("/"):
            href = BASE_URL + href

        elif not href.startswith("http"):
                        )

                    except Exception as e:

                        print(
                            f"⚠️ Erreur traitement annonce : {e}",
                            flush=True
                        )

                    time.sleep(1)

            print(
                "\n😴 Attente de 30 secondes...",
                flush=True
            )

            time.sleep(30)

        except Exception as e:

            print(
                f"❌ Erreur pendant le monitor GCC : {e}",
                flush=True
            )

            time.sleep(30)