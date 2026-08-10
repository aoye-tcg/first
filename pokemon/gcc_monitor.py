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
FIXED_PRICE_URL = "https://gradedcardcenter.com/filtres/fixed-price"

def detect_grader(text):
text_upper = text.upper()

for grader in ALLOWED_GRADERS:
    if grader in text_upper:
        return grader

return None

def extract_grade(text):
match = re.search(
r"\b(?:PSA|PCA|CCC)\s*(?:GRADE\s*)?(\d+(?:[.,]\d+)?)\b",
text,
re.IGNORECASE
)

if match:
    try:
        return float(match.group(1).replace(",", "."))
    except:
        return None

return None

def extract_price(text):
"""
Cherche le prix situé avant 'Prix fixe'.
Exemple :
75 ... 280€ Prix fixe
"""

match = re.search(
    r"(\d+(?:[.,]\d+)?)\s*€\s*Prix fixe",
    text,
    re.IGNORECASE
)

if match:
    try:
        return float(match.group(1).replace(",", "."))
    except:
        return None

return None

def clean_title(text, grader):
"""
Nettoie le texte de l'annonce afin d'éviter
d'envoyer toute la page à price_estimator.
"""

text = re.sub(r"\s+", " ", text).strip()

# On essaie de récupérer uniquement le début
# de l'annonce jusqu'aux informations de prix.
parts = re.split(
    r"\bPrix fixe\b|\bFaire une offre\b|\bAcheter\b",
    text,
    flags=re.IGNORECASE
)

if parts:
    text = parts[0].strip()

# Supprime les nombres isolés correspondant
# au compteur de l'annonce.
text = re.sub(r"\b\d+\s*$", "", text).strip()

return text[:500]

def monitor():

print("🚀 MONITOR GCC : démarrage...", flush=True)

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

    print("🔄 MONITOR GCC : nouveau cycle", flush=True)

    try:

        print(
            "🌐 Connexion à la section Achat à prix fixe...",
            flush=True
        )

        response = session.get(
            FIXED_PRICE_URL,
            timeout=30
        )

        print(
            f"✅ GCC répond : HTTP {response.status_code}",
            flush=True
        )

        if response.status_code != 200:
            print(
                f"⚠️ GCC renvoie HTTP {response.status_code}",
                flush=True
            )

            time.sleep(30)
            continue

        print(
            f"📦 Taille HTML : {len(response.text)} caractères",
            flush=True
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        links = soup.find_all("a", href=True)

        print(
            f"🔗 Nombre de liens trouvés : {len(links)}",
            flush=True
        )

        found = 0

        for link in links:

            try:

                href = link.get("href", "").strip()

                # On ne garde que les vraies annonces.
                if "/item/" not in href:
                    continue

                if href.startswith("/"):
                    url = BASE_URL + href
                else:
                    url = href

                # Évite les doublons dans la même page.
                if url in SEEN:
                    continue

                text = link.get_text(
                    " ",
                    strip=True
                )

                if not text:
                    continue

                # Une annonce à prix fixe doit contenir
                # cette mention.
                if "prix fixe" not in text.lower():
                    continue

                found += 1

                print(
                    f"🎴 Analyse annonce : {url}",
                    flush=True
                )

                grader = detect_grader(text)

                if not grader:

                    print(
                        "⏭️ Gradueur non autorisé ou introuvable",
                        flush=True
                    )

                    continue

                print(
                    f"🏷️ Gradueur détecté : {grader}",
                    flush=True
                )

                # On ne surveille que Pokémon.
                if "pokemon" not in text.lower():

                    print(
                        "⏭️ Ce n'est pas une annonce Pokémon",
                        flush=True
                    )

                    continue

                grade = extract_grade(text)

                price = extract_price(text)

                title = clean_title(
                    text,
                    grader
                )

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

                if price is None:

                    print(
                        "💰 Prix fixe : non détecté",
                        flush=True
                    )

                    continue

                print(
                    f"💰 Prix détecté : {price} €",
                    flush=True
                )

                # L'annonce a été traitée.
                # On la mémorise même si l'estimation
                # n'est pas encore disponible afin
                # d'éviter de la retraiter à chaque cycle.
                SEEN.add(url)

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

                    continue

                print(
                    f"📈 Estimation : {estimated} €",
                    flush=True
                )

                # Bonne affaire si prix <= 75 % de l'estimation.
                if price <= estimated * 0.75:

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
                            f"❌ Erreur Telegram : {e}",
                            flush=True
                        )

                else:

                    print(
                        "⏭️ Pas assez intéressant",
                        flush=True
                    )

            except Exception as e:

                print(
                    f"⚠️ Erreur traitement annonce : {e}",
                    flush=True
                )

        print(
            f"📊 Annonces à prix fixe analysées : {found}",
            flush=True
        )

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
