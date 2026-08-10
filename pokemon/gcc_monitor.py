import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from price_estimator import estimate_price
from telegram_alert import send_alert


SITE_URL = "https://gradedcardcenter.com/"
CHECK_INTERVAL = 30

ALLOWED_GRADERS = {
    "PSA",
    "PCA",
    "COLLECT AURA",
    "CCC"
}

SEEN = set()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}


def get_page(url):
    """Télécharge une page GCC et retourne BeautifulSoup."""

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )


def clean_text(text):
    """Nettoie le texte."""

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def find_grader(text):
    """Cherche un gradueur autorisé dans un texte."""

    text_upper = text.upper()

    # On cherche les plus longs en premier
    for grader in sorted(
        ALLOWED_GRADERS,
        key=len,
        reverse=True
    ):
        if grader in text_upper:
            return grader

    return None


def find_grade(text):
    """Cherche un grade du type PSA 10, PCA 9.5, etc."""

    patterns = [
        r"\b(?:PSA|PCA)\s*(?:GRADE\s*)?(\d+(?:[.,]\d+)?)\b",
        r"\b(?:GRADE|NOTE)\s*[:\-]?\s*(\d+(?:[.,]\d+)?)\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).replace(
                ",",
                "."
            )

    return None


def find_price(text):
    """Essaie de trouver un prix en euros."""

    patterns = [
        r"(\d+(?:[.,]\d+)?)\s*€",
        r"€\s*(\d+(?:[.,]\d+)?)",
        r"(\d+(?:[.,]\d+)?)\s*EUR"
    ]

    values = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for value in matches:

            try:
                price = float(
                    value.replace(
                        ",",
                        "."
                    )
                )

                if price >= 0:
                    values.append(price)

            except ValueError:
                pass

    if not values:
        return None

    # On prend le premier prix trouvé.
    return values[0]


def get_auction_links(soup):
    """Récupère les liens vers les différentes enchères GCC."""

    links = set()

    for link in soup.find_all("a", href=True):

        href = link.get("href")

        if not href:
            continue

        full_url = urljoin(
            SITE_URL,
            href
        )

        if "/filtres/auction/" in full_url:
            links.add(full_url)

    return links


def get_item_links(soup):
    """
    Cherche les liens vers les annonces/articles
    présents dans une page d'enchère.
    """

    links = set()

    for link in soup.find_all("a", href=True):

        href = link.get("href")

        if not href:
            continue

        full_url = urljoin(
            SITE_URL,
            href
        )

        # Les annonces GCC utilisent généralement /item/
        if "/item/" in full_url:
            links.add(full_url)

    return links


def process_item(url):
    """Analyse une annonce individuelle."""

    try:

        print(
            f"🎴 Analyse annonce : {url}",
            flush=True
        )

        soup = get_page(url)

        text = clean_text(
            soup.get_text(
                " ",
                strip=True
            )
        )

        if not text:
            return

        # Recherche du gradueur
        grader = find_grader(text)

        if not grader:

            print(
                "⏭️ Gradueur non autorisé ou introuvable",
                flush=True
            )

            return

        print(
            f"🏷️ Gradueur détecté : {grader}",
            flush=True
        )

        # Nom de l'article
        title = ""

        if soup.title:
            title = clean_text(
                soup.title.get_text()
            )

        # On essaie ensuite les titres visibles
        if not title:

            heading = soup.find(
                ["h1", "h2", "h3"]
            )

            if heading:
                title = clean_text(
                    heading.get_text()
                )

        if not title:
            title = text[:200]

        grade = find_grade(text)

        price = find_price(text)

        print(
            f"🎴 Carte : {title[:150]}",
            flush=True
        )

        print(
            f"🏷️ Gradueur : {grader}",
            flush=True
        )

        print(
            f"📊 Grade : {grade or 'inconnu'}",
            flush=True
        )

        print(
            f"💰 Prix détecté : "
            f"{price if price is not None else 'inconnu'} €",
            flush=True
        )

        # Sans prix, impossible de comparer
        if price is None:

            print(
                "⚠️ Prix introuvable",
                flush=True
            )

            return

        # Estimation de la valeur
        estimated = estimate_price(
            title,
            grader,
            grade
        )

        if estimated is None:

            print(
                "💰 Estimation indisponible",
                flush=True
            )

            return

        print(
            f"💰 Estimation : {estimated} €",
            flush=True
        )

        # Bonne affaire = prix <= 75 % de l'estimation
        if price <= estimated * 0.75:

            if url in SEEN:

                print(
                    "⏭️ Déjà signalée",
                    flush=True
                )

                return

            SEEN.add(url)

            print(
                "🚨 BONNE AFFAIRE DÉTECTÉE !",
                flush=True
            )

            send_alert(
                title,
                price,
                estimated,
                url
            )

    except Exception as e:

        print(
            f"⚠️ Erreur traitement annonce : "
            f"{type(e).__name__}: {e}",
            flush=True
        )


def monitor():

    print(
        "🔎 MONITOR GCC : démarrage...",
        flush=True
    )

    while True:

        try:

            print(
                "🔄 MONITOR GCC : nouveau cycle",
                flush=True
            )

            print(
                "🌐 Connexion à Graded Card Center...",
                flush=True
            )

            soup = get_page(
                SITE_URL
            )

            print(
                "✅ GCC répond correctement",
                flush=True
            )

            # --------------------------------------------------
            # 1. Récupération des enchères
            # --------------------------------------------------

            auction_links = get_auction_links(
                soup
            )

            print(
                f"🔗 Enchères détectées : "
                f"{len(auction_links)}",
                flush=True
            )

            # --------------------------------------------------
            # 2. Analyse des pages d'enchères
            # --------------------------------------------------

            all_item_links = set()

            for auction_url in auction_links:

                try:

                    print(
                        f"🔍 Ouverture enchère : "
                        f"{auction_url}",
                        flush=True
                    )

                    auction_soup = get_page(
                        auction_url
                    )

                    item_links = get_item_links(
                        auction_soup
                    )

                    print(
                        f"📦 Articles trouvés : "
                        f"{len(item_links)}",
                        flush=True
                    )

                    all_item_links.update(
                        item_links
                    )

                except Exception as e:

                    print(
                        f"⚠️ Erreur enchère : {e}",
                        flush=True
                    )

            print(
                f"🎴 Total d'annonces uniques : "
                f"{len(all_item_links)}",
                flush=True
            )

            # --------------------------------------------------
            # 3. Analyse des annonces
            # --------------------------------------------------

            for item_url in all_item_links:

                process_item(
                    item_url
                )

            print(
                f"😴 Attente de {CHECK_INTERVAL} secondes...",
                flush=True
            )

            time.sleep(
                CHECK_INTERVAL
            )

        except Exception as e:

            print(
                f"❌ ERREUR MONITOR GCC : "
                f"{type(e).__name__}: {e}",
                flush=True
            )

            time.sleep(
                CHECK_INTERVAL
            )