import time
import re
import requests
from bs4 import BeautifulSoup

from price_estimator import estimate_price
from telegram_alert import send_alert

ALLOWED_GRADERS = {
"PSA",
"PCA",
"COLLECT AURA",
"CCC"
}

SEEN = set()

BASE_URL = "https://gradedcardcenter.com"
HOME_URL = "https://gradedcardcenter.com/"

def detect_grader(text):
text_upper = text.upper()

for grader in ALLOWED_GRADERS:
    if grader in text_upper:
        return grader

return None

def extract_grade(text):
match = re.search(
r"\b(?:PSA|PCA|CCC)\s*(\d+(?:[.,]\d+)?)\b",
text,
re.IGNORECASE
)

if match:
    try:
        return float(
            match.group(1).replace(",", ".")
        )
    except Exception:
        return None

return None

def extract_price(text):
patterns = [
r"(\d+(?:[.,]\d+)?)\s*€\sPrix fixe",
r"(\d+(?:[.,]\d+)?)\s€"
]

for pattern in patterns:
    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        try:
            return float(
                match.group(1).replace(",", ".")
            )
        except Exception:
            pass

return None

def clean_title(text):
text = re.sub(
r"\s+",
" ",
text
).strip()

# On garde principalement le début
# de l'annonce, avant les informations
# de navigation et de prix.
parts = re.split(
    r"\bGradation\b|\bVends tes articles\b|\bFrançais\b",
    text,
    flags=re.IGNORECASE
)

if parts:
    text = parts[0].strip()

return text[:500]

def analyse_item(session, url):

print(
    f"🎴 Analyse annonce : {url}",
    flush=True
)

try:

    response = session.get(
        url,
        timeout=30
    )

    if response.status_code != 200:

        print(
            f"⚠️ Annonce inaccessible : HTTP {response.status_code}",
            flush=True
        )

        return

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    text = soup.get_text(
        " ",
        strip=True
    )

    if not text:
        return

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

    # On vérifie que l'annonce concerne bien
    # Pokémon.
    if "pokemon" not in text.lower():

        print(
            "⏭️ Pas une carte Pokémon",
            flush=True
        )

        return

    # On cherche le prix fixe.
    price = extract_price(text)

    if price is None:

        print(
            "⏭️ Prix non détecté",
            flush=True
        )

        return

    # Extraction du grade.
    grade = extract_grade(text)

    # Création d'un titre relativement propre.
    title = clean_title(text)

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

    print(
        f"💰 Prix détecté : {price} €",
        flush=True
    )

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

    # Seuil de bonne affaire :
    # prix GCC <= 75 % de l'estimation.
        f"⚠️ Erreur analyse annonce : {e}",
        flush=True
    )

def monitor():

print(
    "🚀 MONITOR GCC : démarrage...",
    flush=True
)

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"
})

while True:

    print(
        "🔄 MONITOR GCC : nouveau cycle",
        flush=True
    )

    try:

        print(
            "🌐 Connexion à Graded Card Center...",
            flush=True
        )

        response = session.get(
            HOME_URL,
        urls = []

        for link in links:

            href = link.get(
                "href",
                ""
            ).strip()

            if "/item/" not in href:
                continue

            if href.startswith("/"):
                url = BASE_URL + href
            elif href.startswith("http"):
                url = href
            else:
                continue

            if url not in urls:
                urls.append(url)

        print(
            f"📊 Nombre d'annonces détectées : {len(urls)}",
            flush=True
        )

        for url in urls:

            if url in SEEN:
                continue

            analyse_item(
                session,
                url
            )

            # On mémorise l'annonce après analyse
            # afin de ne pas la retraiter à chaque cycle.
            SEEN.add(url)

        print(
            "😴 Attente de 30 secondes...",
            flush=True
        )

        time.sleep(30)

    except Exception as e:

        print(
            f"❌ ERREUR MONITOR GCC : "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        print(
            "🔄 Nouvelle tentative dans 30 secondes...",
            flush=True
        )

        time.sleep(30)