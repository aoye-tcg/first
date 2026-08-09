import time
from playwright.sync_api import sync_playwright
from price_estimator import estimate_price
from telegram_alert import send_alert

ALLOWED_GRADERS = {"PSA", "PCA", "COLLECT AURA", "CCC"}
SEEN = set()

def monitor():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while True:
            page.goto("https://gccmarketplace.com/", wait_until="networkidle")

            cards = page.locator("article, .card, .listing")

            for i in range(cards.count()):
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
                    estimated = estimate_price(title, grader, None)

                    if estimated and price <= estimated * 0.75:
                        if title not in SEEN:
                            SEEN.add(title)
                            send_alert(title, price, estimated, "https://gccmarketplace.com/")

                except Exception:
                    pass

            time.sleep(15)