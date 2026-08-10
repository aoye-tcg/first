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
        print("❌ Variables Telegram manquantes")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=20
        )
    except Exception as e:
        print(f"❌ Erreur Telegram : {e}")


@app.route("/")
def home():
    return "Bot Pokémon GCC en ligne"


@app.route("/telegram", methods=["POST"])
def telegram():
    update = request.get_json(force=True)

    message = update.get("message", {})
    text = message.get("text", "")

    print(f"📩 Message Telegram reçu : {text}")

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
    print("🚀 Tentative de démarrage du monitor GCC...")

    try:
        monitor()
    except Exception as e:
        print(f"❌ ERREUR DU MONITOR GCC : {e}")


print("🚀 Lancement du thread GCC...")
monitor_thread = threading.Thread(
    target=start_monitor,
    daemon=True
)

monitor_thread.start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
