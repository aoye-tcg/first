import time
import requests

from price_estimator import estimate_price
from telegram_alert import send_alert


ALLOWED_GRADERS = {
    "PSA",
    "PCA",
    "COLLECT AURA",
    "CCC"
}

SEEN = set()


def monitor():
    print("🔎 MONITOR GCC : démarrage...", flush=True)

    while True:
        try:
            print("🔄 MONITOR GCC : nouveau cycle", flush=True)

            # Test simple de connexion au site GCC
            print("🌐 Test de connexion à GCC Marketplace...", flush=True)

            response = requests.get(
                "https://gccmarketplace.com/",
                timeout=30,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/140.0.0.0 Safari/537.36"
                    )
                }
            )

            print(
                f"✅ GCC répond : HTTP {response.status_code}",
                flush=True
            )

            print(
                f"📦 Taille de la réponse : {len(response.text)} caractères",
                flush=True
            )

            if response.status_code != 200:
                print(
                    f"⚠️ GCC ne renvoie pas HTTP 200 : {response.status_code}",
                    flush=True
                )

            # Pour l'instant on ne lance PAS Playwright.
            # On vérifie simplement que le serveur peut accéder à GCC.

            print(
                "😴 Attente de 30 secondes avant le prochain test...",
                flush=True
            )

            time.sleep(30)

        except Exception as e:
            print(
                f"❌ ERREUR MONITOR GCC : {type(e).__name__}: {e}",
                flush=True
            )

            print(
                "😴 Nouvelle tentative dans 30 secondes...",
                flush=True
            )

            time.sleep(30)
