import time
from playwright.sync_api import sync_playwright
from telegram_alert import send_alert

ALLOWED_GRADERS = {"PSA", "PCA", "COLLECT AURA", "CCC"}
SEEN = set()


def monitor():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while True:
            try:
                page.goto("https://gccmarketplace.com/", wait_until="networkidle")

                cards = page.locator("article, .card, .listing, .product, .product-card")

                for i in range(cards.count()):
                    try:
                        item = cards.nth(i)
                        text = item.inner_text()

                        if "pokemon" not in text.lower():
                            continue

                        grader = None
                        for g in ALLOWED_GRADERS:
                            if g.lower() in text.lower():
                                grader = g
                                break

                        if not grader:
                            continue

                        title = text.split("\n")[0].strip()

                        price = None
                        for line in text.split("\n"):
                            line = line.strip().replace("€", "").replace(",", ".")
                            try:
                                value = float(line)
                                price = value
                                break
                            except Exception:
                                continue

                        if price is None:
                            continue

                        key = f"{title}|{price}"

                        if key in SEEN:
                            continue

                        SEEN.add(key)

                        link = "https://gccmarketplace.com/"
                        send_alert(title, price, price, link)

                    except Exception:
                        continue

            except Exception as e:
                print(f"Erreur scraping GCC : {e}")

            time.sleep(15)