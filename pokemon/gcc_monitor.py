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
        r"\\b(?:PSA|PCA|CCC)\\s*(\\d+(?:[.,]\\d+)?)\\b",
        text,
        re.IGNORECASE,
    )
    if match:
        try:
            return float(match.group(1).replace(",", "."))
        except Exception:
            return None
    return None


def extract_price(text):
    match = re.search(
        r"(\\d+(?:[.,]\\d+)?)\\s*€",
        text,
        re.IGNORECASE,
    )
    if match:
        try:
            return float(match.group(1).replace(",", "."))
        except Exception:
            return None
    return None


def clean_title(text):
    text = re.sub(r"\\s+", " ", text).strip()
    parts = re.split(
        r"\\bPrix fixe\\b|\\bFaire une offre\\b|\\bAcheter\\b",
        text,
        flags=re.IGNORECASE,
    )
    if parts:
        text = parts[0].strip()
    return text[:500]


def analyse_item(session, url):
    print(f"🎴 Analyse annonce : {url}", flush=True)

    response = session.get(url, timeout=30)
    if response.status_code != 200:
        print(
            f"⚠️ Annonce inaccessible : HTTP {response.status_code}",
            flush=True,
        )
        return

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    if "pokemon" not in text.lower():
        return

    grader = detect_grader(text)
    if not grader:
        return

    title = clean_title(text)
    grade = extract_grade(text)
    price = extract_price(text)

    print(f"🏷️ Gradueur détecté : {grader}", flush=True)
    print(f"🎴 Carte : {title}", flush=True)
    print(f"📊 Grade : {grade}", flush=True)
    print(f"💰 Prix détecté : {price} €", flush=True)

    if price is None:
        return

    estimated = estimate_price(title, grader, grade)

    if estimated is None:
        print("💰 Estimation indisponible", flush=True)
        return

    print(f"📈 Estimation : {estimated} €", flush=True)

    if price <= estimated * 0.75:
        print("🚨 BONNE AFFAIRE DÉTECTÉE !", flush=True)
        send_alert(title, price, estimated, url)


def monitor():
    print("🚀 MONITOR GCC : démarrage...", flush=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
    )

    while True:
        try:
            print("🔄 MONITOR GCC : nouveau cycle", flush=True)
            print(
                "🌐 Connexion à GCC Marketplace...",
                flush=True,
            )

            response = session.get(FIXED_PRICE_URL, timeout=30)

            print(
                f"✅ GCC répond : HTTP {response.status_code}",
                flush=True,
            )

            if response.status_code != 200:
                time.sleep(30)
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            item_urls = []

            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                if "/item/" in href:
                    if href.startswith("/"):
                        href = BASE_URL + href
                    if href not in item_urls:
                        item_urls.append(href)

            print(
                f"📦 Nombre d'annonces détectées : {len(item_urls)}",
                flush=True,
            )

            analysed = 0

            for url in item_urls:
                if url in SEEN:
                    continue

                try:
                    analyse_item(session, url)
                    analysed += 1
                    SEEN.add(url)
                except Exception as e:
                    print(
                        f"⚠️ Erreur traitement annonce : {e}",
                        flush=True,
                    )

            print(
                f"📊 Annonces analysées : {analysed}",
                flush=True,
            )
            print("😴 Attente de 30 secondes...", flush=True)
            time.sleep(30)

        except Exception as e:
            print(
                f"❌ ERREUR MONITOR GCC : {type(e).__name__}: {e}",
                flush=True,
            )
            time.sleep(30)