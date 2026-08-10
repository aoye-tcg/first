import time
import requests
from bs4 import BeautifulSoup


def monitor():
    print("🔎 MONITOR GCC : démarrage...", flush=True)

    while True:
        try:
            print("🔄 MONITOR GCC : nouveau cycle", flush=True)
            print("🌐 Connexion à GCC Marketplace...", flush=True)

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
                f"📦 Taille HTML : {len(response.text)} caractères",
                flush=True
            )

            soup = BeautifulSoup(response.text, "html.parser")

            # Recherche de tous les liens présents sur la page
            links = soup.find_all("a")

            print(
                f"🔗 Nombre de liens trouvés : {len(links)}",
                flush=True
            )

            # Affichage des premiers liens intéressants
            displayed = 0

            for link in links:
                text = link.get_text(" ", strip=True)
                href = link.get("href")

                if not text:
                    continue

                print(
                    f"🔎 ÉLÉMENT : {text[:150]}",
                    flush=True
                )

                if href:
                    print(
                        f" 🔗 LIEN : {href}",
                        flush=True
                    )

                displayed += 1

                if displayed >= 20:
                    break

            print(
                f"📊 {displayed} éléments affichés pour diagnostic",
                flush=True
            )

            print(
                "😴 Attente de 30 secondes...",
                flush=True
            )

            time.sleep(30)

        except Exception as e:
            print(
                f"❌ ERREUR MONITOR GCC : "
                f"{type(e).__name__}: {e}",
                flush=True
            )

            time.sleep(30)