import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    }, timeout=20)

@app.route('/')
def home():
    return 'GCC Pokemon Bot online'

@app.route('/telegram', methods=['POST'])
def telegram():
    update = request.get_json(force=True)
    message = update.get('message', {})
    text = message.get('text', '')

    if text == '/start':
        send_message('🤖 GCC Pokémon Deal Bot\\nConnexion réussie !')
    elif text == '/test':
        send_message('🧪 Test réussi ! Les notifications fonctionnent.')

    return 'OK'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000)) 
    app.run(host='0.0.0.0', port=port)