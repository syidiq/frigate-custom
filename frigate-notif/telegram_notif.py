import paho.mqtt.client as mqtt
import json
import requests
from datetime import datetime
import pytz
wib = pytz.timezone('Asia/Jakarta')

# --- KONFIGURASI ---
MQTT_BROKER = "127.0.0.1" # "192.168.90.209" # Sesuaikan dengan IP Broker Anda
IP_SERVER = "45.158.10.170"  # Gunakan localhost jika berjalan di mesin yang sama
MQTT_PORT = 1883
FRIGATE_API_URL = f"http://{IP_SERVER}:5000/api/events"
FRIGATE_API_URL_LOCAL = f"http://{MQTT_BROKER}:5001/api/events"



# --- CONFIG TELEGRAM ---
TELE_TOKEN = "7972577129:AAEzm6U7ZZyIvL-GxuD6lZJrj2zQzt7Rb7s"
TELE_CHAT_ID = "-5216156976"
# "-5216156976" group telegram
# "5997051893" personlal telegram

def send_telegram(label, camera, event_id, score, start_time):
    time_wib = datetime.fromtimestamp(start_time, wib).strftime("%H:%M:%S %d/%m/%Y")

    url_text = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    text = (f"🚨 *DETEKSI BARU {time_wib} *\n\n"
            f"📌 *ID-Object:* {event_id}\n"
            f"📸 *Kamera:* {camera}\n"
            f"🔍 *Objek:* {label.upper()}\n"
            f"📊 *Skor:* {score * 100:.2f}%\n\n"
            f"🔗 [Lihat Video]({FRIGATE_API_URL}/{event_id}/clip.mp4)\n"
            f"🔗 [Lihat Snapshot]({FRIGATE_API_URL}/{event_id}/snapshot.jpg)")

    # Kirim Pesan & Foto
    requests.post(url_text, data={"chat_id": TELE_CHAT_ID, "text": text, "parse_mode": "Markdown"})
    requests.post(f"https://api.telegram.org/bot{TELE_TOKEN}/sendPhoto",
                  data={"chat_id": TELE_CHAT_ID, "photo": f"{FRIGATE_API_URL}/{event_id}/snapshot.jpg"})

sent_events = set()

def on_message(client, userdata, message):
    payload = json.loads(message.payload)
    print(payload)
    if payload['type'] in ['new', 'update']: ##== 'new': # Hanya kirim saat objek pertama kali terdeteksi
        event_id = payload['after']['id']


        if event_id in sent_events:
            print(f"Event {event_id} sudah pernah dikirim, skip")
            return

        label = payload['after']['label']
        camera = payload['after']['camera']
        start_time = payload['after']['start_time']

        after = payload['after']
        # Cek apakah sudah memiliki snapshot
        if not after.get('has_snapshot'):
            print(f"Event {after['id']} belum memiliki snapshot, tunggu update berikutnya")
            return
        
        # Cek apakah objek masuk zona
        if len(after.get('entered_zones', [])) == 0:
            print(f"Event {after['id']} tidak masuk zona, skip")
            return

        # Ambil detail via API (Requests)
        try:
            res = requests.get(f"{FRIGATE_API_URL_LOCAL}/{event_id}")
            if res.status_code == 200:
                print("API Local 0 berhasil diakses","\n")
                score = res.json().get('data').get('top_score',0)
                send_telegram(label, camera, event_id, score, start_time)
                sent_events.add(event_id)
            else:
                print("Gagal mengakses API Frigate untuk event_id:", event_id,"\n")

        except:
            print("Terjadi kesalahan saat mengakses API Frigate untuk event_id:", event_id,"\n")
            pass


client = mqtt.Client()
client.on_message = on_message
try:
    client.connect(MQTT_BROKER, MQTT_PORT)
except Exception as e:
    print(f"Gagal terhubung ke MQTT Broker: {e}")
client.subscribe("frigate/events")
client.loop_forever()





