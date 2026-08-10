import time
from playwright.sync_api import sync_playwright
from price_estimator import estimate_price
from telegram_alert import send_alert

ALLOWED_GRADERS = {"PSA", "PCA", "COLLECT AURA", "CCC"}
SEEN = set()


def monitor():
    print("🔎 Monitor GCC : démarrage de Playwright...", flush=True)

    with sync_playwright() as p:
        print("🔎 Monitor GCC : Playwright démarré", flush=True)

        print("🌐 Monitor GCC : lancement de Chromium...", flush=True)
        print("🌐 Tentative Chromium...", flush=True)

        try:
            browser = p.chromium.launch(
                headless=True,
                timeout=30000,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )

            print("✅ Chromium lancé !", flush=True)

        except Exception as e:
            print(
                f"❌ ERREUR LANCEMENT CHROMIUM : "
                f"{type(e).__name__}: {e}",
                flush=True
            )
            return

        try:
            page = browser.new_page()

            print(
                "🌐 Monitor GCC : ouverture de GCC Marketplace...",
                flush=True
            )

            page.goto(
                "https://gccmarketplace.com/",
                wait_until="networkidle",
                timeout=60000
            )

            print(
                "✅ Monitor GCC : page GCC chargée !",
                flush=True
            )

        except Exception as e:
            print(
                f"❌ ERREUR CHARGEMENT GCC : "
                f"{type(e).__name__}: {e}",
                flush=True
            )
            browser.close()
            return

        while True:
            try:
                page.goto(
                    "https://gccmarketplace.com/",
                    wait_until="networkidle",
                    timeout=60000
                )

            except Exception as e:
                print(
                    f"❌ Erreur pendant le scan GCC : "
                    f"{type(e).__name__}: {e}",
                    flush=True
                )

                time.sleep(15)