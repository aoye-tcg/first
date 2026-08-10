import os
import time
from playwright.sync_api import sync_playwright

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
    print("🔎 Monitor GCC : démarrage de Playwright...", flush=True)

    try:
        with sync_playwright() as p:
            print("🔎 Monitor GCC : Playwright démarré", flush=True)

            # Vérification de l'emplacement des navigateurs Playwright
            browsers_path = os.environ.get(
                "PLAYWRIGHT_BROWSERS_PATH",
                "/opt/render/.cache/ms-playwright"
            )

            print(
                f"🔍 PLAYWRIGHT_BROWSERS_PATH = {browsers_path}",
                flush=True
            )

            print(
                "🌐 Monitor GCC : lancement de Chromium...",
                flush=True
            )

            print(
                "🌐 Tentative Chromium...",
                flush=True
            )

            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            print(
                "✅ Chromium lancé avec succès !",
                flush=True
            )

            page = browser.new_page()

            print(
                "🌐 Ouverture de GCC Marketplace...",
                flush=True
            )

            while True:
                try:
                    print(
                        "🔄 Nouvelle vérification GCC...",
                        flush=True
                    )

                    page.goto(
                        "https://gccmarketplace.com/",
                        wait_until="domcontentloaded",
                        timeout=60000
                    )

                    print(
                        f"✅ Page GCC chargée : {page.title()}",
                        flush=True
                    )

                    cards = page.locator(
                        "article, .card, .listing"
                    )

                    count = cards.count()

                    print(
                        f"🔎 Nombre d'éléments détectés : {count}",
                        flush=True
                    )

                    for i in range(count):
                        try:
                            item = cards.nth(i)

                            title = item.inner_text().strip()

                            if not title:
                                continue

                            if "pokemon" not in title.lower():
                                continue

                            print(
                                f"🎴 Pokémon trouvé : {title[:150]}",
                                flush=True
                            )

                            grader = None

                            for g in ALLOWED_GRADERS:
                                if g.lower() in title.lower():
                                    grader = g
                                    break

                            if not grader:
                                print(
                                    "⏭️ Gradueur non autorisé",
                                    flush=True
                                )
                                continue

                            print(
                                f"🏷️ Gradueur autorisé : {grader}",
                                flush=True
                            )

                            estimated = estimate_price(
                                title,
                                grader,
                                None
                            )

                            if estimated is None:
                                print(
                                    "💰 Estimation indisponible "
                                    "pour le moment",
                                    flush=True
                                )
                                continue

                            print(
                                f"💰 Estimation : {estimated} €",
                                flush=True
                            )

                            # Pour l'instant, on ne déclenche
                            # aucune alerte automatiquement ici,
                            # car le prix réel de l'annonce doit
                            # encore être récupéré correctement.

                        except Exception as e:
                            print(
                                f"⚠️ Erreur traitement annonce : {e}",
                                flush=True
                            )

                    print(
                        "😴 Attente de 15 secondes...",
                        flush=True
                    )

                    time.sleep(15)

                except Exception as e:
                    print(
                        f"❌ Erreur pendant la vérification GCC : {e}",
                        flush=True
                    )

                    time.sleep(15)

    except Exception as e:
        print(
            f"❌ ERREUR MONITOR GCC : "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        raise


if __name__ == "__main__":
    print(
        "🚀 gcc_monitor.py lancé directement",
        flush=True
    )

    monitor()