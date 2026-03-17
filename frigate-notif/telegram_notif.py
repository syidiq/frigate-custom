import paho.mqtt.client as mqtt
import json
import requests
from datetime import datetime
import pytz
wib = pytz.timezone('Asia/Jakarta')

# --- KONFIGURASI ---
IP_SERVER = "45.158.10.170"  # Gunakan localhost jika berjalan di mesin yang sama
MQTT_PORT = 1883
FRIGATE_API_URL = f"http://{IP_SERVER}:5002/api/events"

# --- CONFIG TELEGRAM ---
TELE_TOKEN = "7972577129:AAEzm6U7ZZyIvL-GxuD6lZJrj2zQzt7Rb7s"
TELE_CHAT_ID = "5997051893"

def send_telegram(label, camera, event_id, score, start_time):
    time_wib = datetime.fromtimestamp(start_time, wib).strftime("%H:%M:%S %d/%m/%Y")

    url_text = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    text = (f"🚨 *DETEKSI BARU {time_wib} *\n\n"
            f"📸 *Kamera:* {camera}\n"
            f"🔍 *Objek:* {label.upper()}\n"
            f"📊 *Skor:* {score * 100:.2f}%\n\n"
            f"🔗 [Lihat Video]({FRIGATE_API_URL}/{event_id}/clip.mp4)")

    # Kirim Pesan & Foto
    requests.post(url_text, data={"chat_id": TELE_CHAT_ID, "text": text, "parse_mode": "Markdown"})
    requests.post(f"https://api.telegram.org/bot{TELE_TOKEN}/sendPhoto",
                  data={"chat_id": TELE_CHAT_ID, "photo": f"{FRIGATE_API_URL}/{event_id}/snapshot.jpg"})

def on_message(client, userdata, message):
    payload = json.loads(message.payload)
    print(payload)
    if payload['type'] == 'new': # Hanya kirim saat objek pertama kali terdeteksi
        event_id = payload['after']['id']
        label = payload['after']['label']
        camera = payload['after']['camera']
        start_time = payload['after']['start_time']

        # Ambil detail via API (Requests)
        try:
            res = requests.get(f"{FRIGATE_API_URL}/{event_id}")
            if res.status_code == 200:
                score = res.json().get('top_score', 0)
                send_telegram(label, camera, event_id, score, start_time)
        except:
            pass




# Test Area =============================================================================================

payload = {}
headers = {'Accept': 'application/json'}
response = requests.request("GET", FRIGATE_API_URL, headers=headers, data=payload)

# print(response.text)
payload = json.loads(response.text)
nu = 1
event_id = payload[nu]['id']
label = payload[nu]['label']
camera = payload[nu]['camera']
start_time = payload[nu]['start_time']

# Ambil detail via API (Requests)
try:
    res = requests.get(f"{FRIGATE_API_URL}/{event_id}")
    if res.status_code == 200:
        score = res.json().get('top_score', 0.6793)
        send_telegram(label, camera, event_id, score, start_time)
except:
    pass



# Mulai MQTT Client =============================================================================================


# client = mqtt.Client()
# client.on_message = on_message
# client.connect(IP_SERVER, MQTT_PORT)
# client.subscribe("frigate/events")
# client.loop_forever()