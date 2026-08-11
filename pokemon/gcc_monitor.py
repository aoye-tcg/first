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
        r"(?:PSA|PCA|CCC|COLLECT AURA)\\s*(\\d+(?:[.,]\\d+)?)",
        text,
        re.IGNORECASE
    )
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def extract_price(text):
    prices = re.findall(
        r"(\\d+(?:[.,]\\d+)?)\\s*€",
        text,
        re.IGNORECASE
    )
    if prices:
        return float(prices[0].replace(",", "."))
    return None


def clean_title(text):
    text = re.sub(r"\\s+", " ", text).strip()
    parts = re.split(
        r"\\bPrix fixe\\b|\\bFaire une offre\\b|\\bAcheter\\b",
        text,
        flags=re.IGNORECASE
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
            flush=True
    })

    while True:
        try:
            print("🔄 MONITOR GCC : nouveau cycle", flush=True)
            print(
                "🌐 Connexion à GCC Marketplace...",
                flush=True
            )

            response = session.get(FIXED_PRICE_URL, timeout=30)

            print(
                f"✅ GCC répond : HTTP {response.status_code}",
                flush=True
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
                flush=True
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
                        flush=True
                    )

            print(
                f"📊 Annonces analysées : {analysed}",
                flush=True
            )
            print("😴 Attente de 30 secondes...", flush=True)
            time.sleep(30)

        except Exception as e:
            print(
                f"❌ ERREUR MONITOR GCC : {type(e).__name__}: {e}",
                flush=True
            )
            time.sleep(30)