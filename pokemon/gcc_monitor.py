import time
import requests
from bs4 import BeautifulSoup


SITE_URL = "https://gradedcardcenter.com/"

ALLOWED_GRADERS = {
    "PSA",
    "PCA",
    "COLLECT AURA",
    "CCC"
}


def monitor():
    print("🔎 MONITOR GCC : démarrage...", flush=True)

    while True:
        try:
            print("🔄 MONITOR GCC : nouveau cycle", flush=True)
            print("🌐 Connexion à Graded Card Center...", flush=True)

            response = requests.get(
                SITE_URL,
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

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            # Texte complet de la page
            text = soup.get_text(
                " ",
                strip=True
            )

            print(
                f"📝 Taille texte visible : {len(text)} caractères",
                flush=True
            )

            # Recherche des gradueurs autorisés
            print(
                "🔍 Recherche des gradueurs autorisés...",
                flush=True
            )

            found = 0

            for grader in ALLOWED_GRADERS:

                position = 0

                while True:

                    position = text.lower().find(
                        grader.lower(),
                        position
                    )

                    if position == -1:
                        break

                    found += 1

                    start = max(
                        0,
                        position - 250
                    )

                    end = min(
                        len(text),
                        position + 500
                    )

                    extrait = text[start:end]

                    print(
                        f"\n🏷️ GRADUEUR TROUVÉ : {grader}",
                        flush=True
                    )

                    print(
                        f"📄 Extrait : {extrait}",
                        flush=True
                    )

                    position += len(grader)

                    # Évite d'inonder les logs
                    if found >= 20:
                        break

                if found >= 20:
                    break

            print(
                f"\n📊 Nombre de résultats affichés : {found}",
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
