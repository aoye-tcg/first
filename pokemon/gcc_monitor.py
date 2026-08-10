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

        browser = p.chromium.launch(
            headless=True,
            timeout=30000
        )

        print("✅ Chromium lancé !", flush=True)

        page = browser.new_page()

        print("🌐 Monitor GCC : ouverture de GCC Marketplace...", flush=True)

        while True:
            try:
                page.goto(
                    "https://gccmarketplace.com/",
                    wait_until="networkidle",
                    timeout=60000
                )

                print("✅ Monitor GCC : page GCC chargée", flush=True)

                cards = page.locator("article, .card, .listing")
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

                        price = 0.0

                        estimated = estimate_price(
                            title,
                            grader,
                            None
                        )

                        if estimated and price <= estimated * 0.75:
                            if title not in SEEN:
                                SEEN.add(title)

                                send_alert(
                                    title,
                                    price,
                                    estimated,
                                    "https://gccmarketplace.com/"
                                )

                                print(
                                    f"🚨 Bonne affaire détectée : {title}",
                                    flush=True
                                )

                    except Exception as e:
                        print(
                            f"⚠️ Erreur traitement annonce : {e}",
                            flush=True
                        )

                print(
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