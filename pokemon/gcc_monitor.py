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

            print("🌐 Monitor GCC : lancement de Chromium...", flush=True)

            browser = p.chromium.launch(headless=True)

            print("✅ Monitor GCC : Chromium lancé", flush=True)

            page = browser.new_page()

            print("✅ Monitor GCC : nouvelle page créée", flush=True)

            while True:
                try:
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
                        "✅ Monitor GCC : page GCC chargée",
                        flush=True
                    )

                    cards = page.locator(
                        "article, .card, .listing"
                    )

                    count = cards.count()

                    print(
                        f"🔎 Monitor GCC : {count} éléments détectés",
                        flush=True
                    )

                    for i in range(count):
                        try:
                            item = cards.nth(i)
                            title = item.inner_text()

                            if "pokemon" not in title.lower():
                                continue

                            grader = None

                            for g in ALLOWED_GRADERS:
                                if g.lower() in title.lower():
                                    grader = g
                                    break

                            if not grader:
                                continue

                            print(
                                f"🎴 Carte Pokémon détectée : {title[:150]}",
                                flush=True
                            )

                            print(
                                f"🏷️ Grader détecté : {grader}",
                                flush=True
                            )

                            # Pour l'instant le prix réel n'est pas encore
                            # récupéré depuis GCC.
                            price = 0.0

                            estimated = estimate_price(
                                title,
                                grader,
                                None
                            )

                            if estimated and price <= estimated * 0.75:

                                if title not in SEEN:
                                    SEEN.add(title)

                                    print(
                                        f"🚨 Bonne affaire détectée : {title}",
                                        flush=True
                                    )

                                    send_alert(
                                        title,
                                        price,
                                        estimated,
                                        "https://gccmarketplace.com/"
                                    )

                        except Exception as e:
                            print(
                                f"⚠️ Erreur lors du traitement d'une annonce : {e}",
                                flush=True
                            )

                    print(
                        "⏳ Monitor GCC : nouvelle vérification dans 15 secondes...",
                        flush=True
                    )

                    time.sleep(15)

                except Exception as e:
                    print(
                        f"❌ Erreur lors du chargement de GCC : {e}",
                        flush=True
                    )

                    print(
                        "⏳ Nouvelle tentative dans 30 secondes...",
                        flush=True
                    )

                    time.sleep(30)

    except Exception as e:
        print(
            f"❌ ERREUR CRITIQUE DU MONITOR GCC : {e}",
            flush=True
        )
