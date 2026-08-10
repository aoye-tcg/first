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


def detect_grader(text):
    text_upper = text.upper()

    # On cherche les gradueurs les plus spécifiques
    # avant les noms courts.
    if "COLLECT AURA" in text_upper:
        return "COLLECT AURA"

    if "PSA" in text_upper:
        return "PSA"

    if "PCA" in text_upper:
        return "PCA"

    if re.search(r"\bCCC\b", text_upper):
        return "CCC"

    return None


def detect_price(text):
    """
    Cherche un prix en euros dans le texte.
    Exemples acceptés :
    30 €
    30€
    30,00 €
    30.00€
    """

    patterns = [
        r"(\d+(?:[.,]\d{1,2})?)\s*€",
        r"€\s*(\d+(?:[.,]\d{1,2})?)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            try:
                value = match.group(1).replace(",", ".")
                return float(value)
            except ValueError:
                pass

    return None


def extract_grade(text):
    """
    Cherche un grade du type :
    PSA 10
    PCA 9.5
    PCA 9,5
    """

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


def clean_text(text):
    return " ".join(text.split())


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

    grade = extract_grade(text)

    # --------------------------------------------------------
    # Tentative de récupération du titre
    # --------------------------------------------------------

    title = None

    for selector in [
        "h1",
        "h2",
        "[class*='title']",
        "[class*='name']"
    ]:
        element = soup.select_one(selector)

        if element:
            candidate = clean_text(
                element.get_text(" ", strip=True)
            )

            if candidate:
                title = candidate
                break

    if not title:
        title = text[:250]

    print(
        f"🎴 Carte : {title}",
        flush=True
    )

    print(
        f"🏷️ Gradueur : {grader}",
        flush=True
    )

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
    # Prix
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
    # Estimation
    # --------------------------------------------------------

    try:
        estimated = estimate_price(
            title,
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
    # Détection bonne affaire
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
                title,
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
# RÉCUPÉRATION DES ANNONCES FIXED PRICE
# ============================================================

def get_fixed_price_listings():
    print(
        "🌐 Connexion à la page ACHAT À PRIX FIXE...",
        flush=True
    )

    response = get_page(FIXED_PRICE_URL)

    if response is None:
        return []

    print(
        f"✅ GCC répond : HTTP {response.status_code}",
        flush=True
    )

    print(
        f"📦 Taille HTML : {len(response.text)} caractères",
        flush=True
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    links = []

    for a in soup.find_all("a", href=True):

        href = a.get("href", "").strip()

        if not href:
            continue

        # On ne garde que les liens vers des annonces
        if "/item/" not in href:
            continue

        if href.startswith("/"):
            href = BASE_URL + href

        elif href.startswith("http"):
            pass

        else:
            continue

        if href not in links:
            links.append(href)

    return links


# ============================================================
# MONITOR PRINCIPAL
# ============================================================

def monitor():

    print(
        "🔎 MONITOR GCC : démarrage...",
        flush=True
    )

    while True:

        try:

            print(
                "\n🔄 MONITOR GCC : nouveau cycle",
                flush=True
            )

            links = get_fixed_price_listings()

            print(
                f"🛒 Annonces à prix fixe trouvées : {len(links)}",
                flush=True
            )

            if not links:

                print(
                    "⚠️ Aucune annonce trouvée.",
                    flush=True
                )

            else:

                for url in links:

                    try:
                        analyse_listing(url)

                    except Exception as e:

                        print(
                            f"⚠️ Erreur traitement annonce : {e}",
                            flush=True
                        )

                    # Petite pause pour éviter de bombarder GCC
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