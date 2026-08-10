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

        try:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )

            print("✅ Monitor GCC : Chromium lancé", flush=True)

        except Exception as e:
            print(f"❌ ERREUR Chromium : {type(e).__name__}: {e}", flush=True)
                    "⏳ Nouvelle vérification dans 15 secondes...",
                    flush=True
                )

                time.sleep(15)

            except Exception as e:
                print(
                    f"❌ Erreur pendant le scan GCC : "
                    f"{type(e).__name__}: {e}",
                    flush=True
                )

                time.sleep(15)
