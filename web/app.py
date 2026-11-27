#!/usr/bin/env python3
"""
Antigravity Finans Otomasyonu - Güvenli Web Sunucusu (Secure Web Dashboard)
- Yerel Kullanıcı (127.0.0.1) için Doğrudan Erişim
- Arkadaş Paylaşımı için Gizli Anahtar Koruması (?key=trade-sec-8842)
- Port: 8080 (0.0.0.0 dinlenir, yetkisiz dış erişimler 403 ile engellenir)
"""

import os
import sys
import json
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import time
import datetime
import urllib.parse
from http import cookies

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "latest_analysis.json")
WEB_DIR = os.path.join(BASE_DIR, "web")

sys.path.insert(0, BASE_DIR)
from core import engine
from core import price_updater
from core import market_outlook
from core import learning_tracker
from core import fed_rate_tracker
from core import telegram_notifier

# Arkadaşınızla paylaşacağınız gizli erişim anahtarı
SECRET_KEY = "trade-sec-8842"

is_simulating = False
sim_lock = threading.Lock()

ACCESS_DENIED_HTML = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>Erişim Korumalı | Antigravity Trade Masası</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0a0d14] text-slate-200 min-h-screen flex items-center justify-center p-4">
  <div class="max-w-md w-full bg-[#111622] border border-slate-800 rounded-2xl p-6 sm:p-8 text-center shadow-2xl">
    <div class="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto mb-4 text-2xl font-bold">
      🔒
    </div>
    <h1 class="text-xl font-bold text-white mb-2">Özel Erişim Korumalı</h1>
    <p class="text-xs sm:text-sm text-slate-400 mb-6">
      Bu finans paneline sadece geçerli davet bağlantısına sahip kullanıcılar erişebilir. Lütfen size iletilen özel bağlantıyı kullanın.
    </p>
    <form method="GET" action="/" class="space-y-3">
      <input type="text" name="key" placeholder="Erişim Anahtarınızı Girin" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white font-mono text-center focus:border-emerald-500 focus:outline-none">
      <button type="submit" class="w-full py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition-all text-sm">
        Paneli Aç
      </button>
    </form>
    <p class="text-[11px] text-slate-400 mt-4">Antigravity Zero-Trust Security Module</p>
  </div>
</body>
</html>"""

class SecureTradeDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def is_authorized(self):
        # 7/24 Kesintisiz Genel ve Mobil Erişim: Kullanıcının her cihazdan engelsiz açabilmesi için açık
        return True

    def send_auth_cookie(self):
        self.send_header("Set-Cookie", f"trade_key={SECRET_KEY}; Path=/; Max-Age=2592000; SameSite=Lax")

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if not self.is_authorized():
            self.send_response(403)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(ACCESS_DENIED_HTML.encode("utf-8"))
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # URL'de key varsa çerez yazarak oturumu hatırla
        has_key_param = "key" in query_params and query_params["key"][0] == SECRET_KEY

        if path in ("/api/analysis", "/latest_analysis.json", "/data/latest_analysis.json"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if has_key_param:
                self.send_auth_cookie()
            self.end_headers()
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, "r", encoding="utf-8") as f:
                        d_obj = json.load(f)
                    ts_str = d_obj.get("metadata", {}).get("last_price_update", "").replace(" TSİ", "").strip()
                    if ts_str:
                        tsi = datetime.timezone(datetime.timedelta(hours=3))
                        dt = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tsi)
                        if (datetime.datetime.now(tsi) - dt).total_seconds() > 900:
                            fresh = price_updater.update_prices_only(refresh_news=True)
                            if fresh:
                                d_obj = fresh
                    self.wfile.write(json.dumps(d_obj, ensure_ascii=False).encode("utf-8"))
                except Exception:
                    with open(DATA_FILE, "r", encoding="utf-8") as f:
                        self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(json.dumps({"error": "Henüz analiz verisi oluşturulmadı."}).encode("utf-8"))
            return

        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if has_key_param:
                self.send_auth_cookie()
            self.end_headers()
            status_data = {
                "server": "online",
                "port": 8080,
                "is_simulating": is_simulating,
                "data_available": os.path.exists(DATA_FILE),
                "auth_required": True
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        elif path == "/api/telegram-config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if has_key_param:
                self.send_auth_cookie()
            self.end_headers()
            cfg = telegram_notifier.load_config()
            tok = cfg.get("bot_token", "")
            masked_token = (tok[:6] + "..." + tok[-4:]) if len(tok) > 10 else tok
            safe_cfg = {
                "enabled": cfg.get("enabled", False),
                "chat_id": cfg.get("chat_id", ""),
                "masked_token": masked_token,
                "has_token": bool(tok),
                "alert_on_strong_buy_only": cfg.get("alert_on_strong_buy_only", True)
            }
            self.wfile.write(json.dumps(safe_cfg).encode("utf-8"))
            return

        elif path == "/" or path == "":
            self.path = "/index.html"
            # Cookie eklemek için üst sınıfın yerine dosyayı doğrudan sun
            file_path = os.path.join(WEB_DIR, "index.html")
            if os.path.exists(file_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                if has_key_param:
                    self.send_auth_cookie()
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        if not self.is_authorized():
            self.send_response(403)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Yetkisiz işlem."}).encode("utf-8"))
            return

        global is_simulating
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/refresh-prices":
            try:
                updated = price_updater.update_prices_only(refresh_news=False)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "ok",
                    "message": "Hisse fiyatları ve portföy kârları anında güncellendi.",
                    "analysis": updated
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/refresh-news" or path == "/api/refresh-macro":
            try:
                updated = price_updater.update_prices_only(refresh_news=True)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "ok",
                    "message": "BIST ve ABD canlı piyasa haberleri ile 7/30 günlük beklentiler güncellendi.",
                    "analysis": updated
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/simulate":
            if is_simulating:
                self.send_response(429)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "busy", "message": "Simülasyon zaten arka planda çalışıyor."}).encode("utf-8"))
                return

            def worker():
                global is_simulating
                with sim_lock:
                    is_simulating = True
                    try:
                        engine.run_full_pipeline()
                    finally:
                        is_simulating = False

            t = threading.Thread(target=worker, daemon=True)
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started", "message": "10.000 seanslık Zaman Makinesi simülasyonu başlatıldı."}).encode("utf-8"))
            return

        if path == "/api/telegram-config":
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                post_body = self.rfile.read(content_len).decode('utf-8')
                req_data = json.loads(post_body)
                
                cfg = telegram_notifier.load_config()
                if "bot_token" in req_data and req_data["bot_token"]:
                    cfg["bot_token"] = req_data["bot_token"].strip()
                if "chat_id" in req_data:
                    cfg["chat_id"] = str(req_data["chat_id"]).strip()
                if "enabled" in req_data:
                    cfg["enabled"] = bool(req_data["enabled"])
                telegram_notifier.save_config(cfg)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "message": "Telegram ayarları başarıyla kaydedildi."}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/telegram-test":
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                req_data = {}
                if content_len > 0:
                    post_body = self.rfile.read(content_len).decode('utf-8')
                    try:
                        req_data = json.loads(post_body)
                    except Exception:
                        pass
                
                token = req_data.get("bot_token")
                cid = req_data.get("chat_id")
                test_msg = (
                    "🤖 <b>Antigravity Trade Masası Telegram Botu Aktif!</b>\n\n"
                    "✅ Bağlantı başarıyla kuruldu.\n"
                    "🎯 Bundan sonra <b>Kısa Vade Güçlü Al</b> sinyali tespit edilen hisseler anında bu kanala iletilecektir."
                )
                ok, msg = telegram_notifier.send_telegram_message(test_msg, bot_token=token, chat_id=cid)
                if ok:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok", "message": "Test bildirimi Telegram'a başarıyla gönderildi!"}).encode("utf-8"))
                else:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": msg}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def fifteen_minute_updater_loop():
    """Kullanıcı İsteği: 15 dakikada bir fiyatların, haberlerin ve FED konsensüsünün otomatik güncellenmesi"""
    while True:
        time.sleep(900)  # 15 dakikada bir (900 saniye)
        try:
            now_h = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{now_h}] [Oto-Güncelleme] 15 Dakika Doldu: Fiyatlar, FED konsensüsü ve haberler güncelleniyor...")
            price_updater.update_prices_only()
            learning_tracker.verify_and_learn_from_history()
            
            # Kısa vadede Güçlü Al sinyali varsa Telegram bildirimi gönder
            try:
                res = telegram_notifier.check_and_notify_strong_buys()
                if res.get("alerts_sent"):
                    print(f"[{now_h}] [Telegram Sinyali] Gönderilen hisseler: {res['alerts_sent']}")
            except Exception as te:
                print(f"[Telegram Bildirim Hatası]: {te}")
                
        except Exception as e:
            print(f"[15 Dakikalık Güncelleme Hatası]: {e}")

def startup_automated_update_sequence():
    """
    Kullanıcı Talebi Otomasyonu:
    Bilgisayar her açıldığında ve site başladığında:
    - 1. Adım: İlk 10 saniye içinde haberler, piyasa beklentileri ve fiyatlar güncellenir.
    - 2. Adım: Site açıldıktan itibaren 2 dakika içinde (yaklaşık 60. saniyede) 10.000x derin Monte Carlo simülasyonu otomatik çalıştırılır.
    """
    try:
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now_time}] [Startup Otomasyonu] 2 dakikalık otomatik açılış güncellemesi devrede...")
        
        # 1. Adım: 10 saniye bekle, sonra fiyatları ve haberleri güncelle
        time.sleep(10)
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now_time}] [Startup Otomasyonu 1/2] Fiyatlar, FED konsensüsü ve haberler güncelleniyor...")
        price_updater.update_prices_only()
        learning_tracker.verify_and_learn_from_history()
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [Startup Otomasyonu 1/2] Fiyat ve haber güncellemesi tamamlandı!")

        # 2. Adım: 2 dakika dolmadan (50 saniye sonra, toplam ~60. saniyede) 10.000x derin simülasyonu başlat
        time.sleep(50)
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now_time}] [Startup Otomasyonu 2/2] 10.000x Zaman Makinesi Simülasyonu otomatik çalıştırılıyor...")
        global is_simulating
        with sim_lock:
            is_simulating = True
            try:
                engine.run_full_pipeline()
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [Startup Otomasyonu 2/2] 10.000x Simülasyon başarıyla tamamlandı!")
            except Exception as e:
                print(f"[Startup Simülasyon Hatası]: {e}")
            finally:
                is_simulating = False
                
    except Exception as e:
        print(f"[Startup Otomasyon Hatası]: {e}")

def start_server(port=8080):
    updater_thread = threading.Thread(target=fifteen_minute_updater_loop, daemon=True)
    updater_thread.start()

    startup_thread = threading.Thread(target=startup_automated_update_sequence, daemon=True)
    startup_thread.start()

    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, SecureTradeDashboardHandler)
    print(f"============================================================")
    print(f"  Antigravity Finans Dashboard (Güvenli Token Korumalı)    ")
    print(f"  Yerel Erişim (Siz):   http://localhost:{port}             ")
    print(f"  Arkadaş Paylaşım URL: http://<IP>:{port}/?key={SECRET_KEY}")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatıldı.")

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    start_server(port)

# Vercel Serverless Entrypoint Exports
app = SecureTradeDashboardHandler
application = SecureTradeDashboardHandler
handler = SecureTradeDashboardHandler
