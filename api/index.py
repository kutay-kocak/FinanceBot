from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import urllib.parse
from http import cookies

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "latest_analysis.json")
SECRET_KEY = "trade-sec-8842"

sys.path.insert(0, BASE_DIR)
try:
    from core import price_updater
    from core import market_outlook
    from core import learning_tracker
    from core import fed_rate_tracker
except Exception:
    price_updater = None
    market_outlook = None
    learning_tracker = None
    fed_rate_tracker = None

class handler(BaseHTTPRequestHandler):
    def is_authorized(self):
        # Güvenlik duvarı kaldırıldı, doğrudan linksiz de 7/24 engelsiz erişim
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
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Erişim izni yok. Geçerli ?key parametresi gereklidir."}).encode("utf-8"))
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.endswith("/status"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_auth_cookie()
            self.end_headers()
            status_data = {
                "server": "online",
                "platform": "Vercel Cloud 7/24 Kesintisiz",
                "is_simulating": False,
                "data_available": os.path.exists(DATA_FILE),
                "auth_required": True
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        elif path.endswith("/analysis"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_auth_cookie()
            self.end_headers()
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(json.dumps({"error": "Henüz analiz verisi oluşturulmadı."}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if not self.is_authorized():
            self.send_response(403)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Yetkisiz işlem."}).encode("utf-8"))
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.endswith("/refresh-prices"):
            if price_updater:
                try:
                    price_updater.update_prices_only()
                except Exception as e:
                    print(f"Update error: {e}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Fiyatlar güncellendi."}).encode("utf-8"))
            return

        if path.endswith("/refresh-news") or path.endswith("/refresh-macro"):
            if price_updater:
                try:
                    price_updater.update_prices_only()
                except Exception as e:
                    print(f"Update error: {e}")
            if learning_tracker:
                try:
                    learning_tracker.verify_and_learn_from_history()
                except Exception as e:
                    print(f"Learning error: {e}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Piyasa haberleri ve beklentiler güncellendi."}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

# Vercel entrypoint exports
app = handler
application = handler
