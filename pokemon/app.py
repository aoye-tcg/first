import os
import threading
import requests
from flask import Flask, request

from gcc_monitor import monitor

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Variables Telegram manquantes", flush=True)
        return

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=20
        )

    except Exception as e:
        print(f"❌ Erreur Telegram : {e}", flush=True)


@app.route("/")
def home():
    return "GCC Pokemon Bot online"


@app.route("/telegram", methods=["POST"])
def telegram():
    update = request.get_json(force=True)

    message = update.get("message", {})
    text = message.get("text", "")

    print(f"📩 Message Telegram reçu : {text}", flush=True)

    if text == "/start":
        send_message(
            "🤖 GCC Pokémon Deal Bot\n"
            "Connexion réussie !"
        )

    elif text == "/test":
        send_message(
            "🧪 Test réussi ! Les notifications fonctionnent."
        )

    return "OK"


def start_monitor():
    print("🚀 Tentative de démarrage du monitor GCC...", flush=True)

    try:
        monitor()

    except Exception as e:
        print(
            f"❌ ERREUR MONITOR GCC : "
            f"{type(e).__name__}: {e}",
            flush=True
        )


print("🚀 Lancement du thread GCC...", flush=True)

thread = threading.Thread(
    target=start_monitor,
    daemon=True
)

thread.start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )