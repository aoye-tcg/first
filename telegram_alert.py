import os
import requests

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_alert(title, price, estimated, link):
    text = (
        f"🔴 Bonne affaire détectée\\n\\n"
        f"{title}\\n"
        f"Prix GCC : {price} €\\n"
        f"Valeur estimée : {estimated} €\\n"
        f"Décote : {round((1 - price/estimated)*100)} %\\n\\n"
        f"{link}"
    )

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=20
    )