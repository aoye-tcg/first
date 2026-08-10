import os
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

        chromium_path = (
            "/opt/render/.cache/ms-playwright/"
            "chromium-1187/chrome-linux/chrome"
        )

        print(
            f"🌐 Chromium recherché : {chromium_path}",
            flush=True
        )

        if not os.path.exists(chromium_path):
            print(
                "❌ Chromium complet introuvable !",
                flush=True
            )
            return

        print(
            "✅ Chromium complet trouvé !",
            flush=True
        )

        print(
            "🌐 Tentative de lancement de Chromium...",
            flush=True
        )

        try:
            browser = p.chromium.launch(
                executable_path=chromium_path,
                headless=True,
                timeout=30000,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )

            print(
                "✅ Chromium lancé avec succès !",
                    f"{count} éléments détectés",
                                    f"{title}",
                                    flush=True
                                )

                    except Exception as e:
                        print(
                            f"⚠️ Erreur traitement annonce : {e}",
                            flush=True
                        )

                print(
                    "⏳ Nouvelle vérification "
                    "dans 15 secondes...",
                    flush=True
                )

                time.sleep(15)

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