#!/usr/bin/env python3
"""
Antigravity Finans Otomasyonu - Vercel & Yerel Sunucu Giriş Noktası (app.py)
Exports 'app', 'application', and 'handler' as required by Vercel Python runtime.
Desteklenen ortamlar: Vercel Cloud, Yerel Python (python app.py), Docker.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import sys
import types
import urllib.parse
from http import cookies

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Dosya yapısı uyumluluğu: Hem düz (root) hem klasörlü (core/, data/, web/) yapıları destekle
if "core" not in sys.modules:
    core_pkg = types.ModuleType("core")
    core_dir = os.path.join(BASE_DIR, "core")
    core_pkg.__path__ = [core_dir] if os.path.exists(core_dir) else [BASE_DIR]
    sys.modules["core"] = core_pkg

sys.path.insert(0, BASE_DIR)
if os.path.exists(os.path.join(BASE_DIR, "core")):
    sys.path.insert(0, os.path.join(BASE_DIR, "core"))

try:
    import price_updater
except Exception:
    try:
        from core import price_updater
    except Exception:
        price_updater = None

try:
    import learning_tracker
except Exception:
    try:
        from core import learning_tracker
    except Exception:
        learning_tracker = None

try:
    import telegram_notifier
except Exception:
    try:
        from core import telegram_notifier
    except Exception:
        telegram_notifier = None

# Dosya yollarını dinamik çöz (Düz dizin veya alt klasör)
def find_file(filename, subfolders=None):
    candidates = [os.path.join(BASE_DIR, filename)]
    if subfolders:
        for sf in subfolders:
            candidates.append(os.path.join(BASE_DIR, sf, filename))
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

DATA_FILE = find_file("latest_analysis.json", ["data"])
CONFIG_FILE = find_file("telegram_config.json", ["data"])
INDEX_HTML = find_file("index.html", ["public", "web"])
SECRET_KEY = "trade-sec-8842"

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
      Bu finans paneline sadece yetkili kullanıcılar erişebilir. Lütfen size iletilen özel bağlantıyı kullanın veya anahtarınızı girin.
    </p>
    <form method="GET" action="/" class="space-y-3">
      <input type="text" name="key" placeholder="Erişim Anahtarınızı Girin" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white font-mono text-center focus:border-emerald-500 focus:outline-none">
      <button type="submit" class="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-2 rounded-lg transition-colors">
        Masayı Aç
      </button>
    </form>
  </div>
</body>
</html>"""

class SecureTradeDashboardHandler(BaseHTTPRequestHandler):
    def is_authorized(self):
        # 127.0.0.1 yerel kullanıcıya tam erişim
        client_ip = self.client_address[0] if self.client_address else ""
        if client_ip in ("127.0.0.1", "localhost", "::1"):
            return True

        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        # URL'de ?key=trade-sec-8842 var mı?
        if "key" in query and query["key"][0] == SECRET_KEY:
            return True

        # Daha önce oturum açmış mı? (Cookie kontrolü)
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            c = cookies.SimpleCookie(cookie_header)
            if "trade_key" in c and c["trade_key"].value == SECRET_KEY:
                return True

        return False

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
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        has_key_param = "key" in query and query["key"][0] == SECRET_KEY

        # Ana sayfa isteği
        if path in ("/", "/index.html", ""):
            if not self.is_authorized():
                self.send_response(403)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(ACCESS_DENIED_HTML.encode("utf-8"))
                return

            html_target = find_file("index.html", ["public", "web"])
            if os.path.exists(html_target):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                if has_key_param:
                    self.send_auth_cookie()
                self.end_headers()
                with open(html_target, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"index.html bulunamadi.")
                return

        # Statik dosyalar
        safe_name = path.lstrip("/")
        local_asset = find_file(safe_name, ["public", "web"])
        if os.path.isfile(local_asset):
            self.send_response(200)
            if local_asset.endswith(".html"):
                self.send_header("Content-Type", "text/html; charset=utf-8")
            elif local_asset.endswith(".js"):
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
            elif local_asset.endswith(".css"):
                self.send_header("Content-Type", "text/css; charset=utf-8")
            elif local_asset.endswith(".json"):
                self.send_header("Content-Type", "application/json; charset=utf-8")
            if has_key_param:
                self.send_auth_cookie()
            self.end_headers()
            with open(local_asset, "rb") as f:
                self.wfile.write(f.read())
            return

        # API yetki kontrolü
        if not self.is_authorized():
            self.send_response(403)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Erişim izni yok. Geçerli ?key parametresi gereklidir."}).encode("utf-8"))
            return

        # API: Analiz Verisi
        if path.endswith("/analysis"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if has_key_param:
                self.send_auth_cookie()
            self.end_headers()
            data_target = find_file("latest_analysis.json", ["data"])
            if os.path.exists(data_target):
                with open(data_target, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(json.dumps({"error": "Henüz analiz verisi oluşturulmadı."}).encode("utf-8"))
            return

        # API: Durum
        elif path.endswith("/status"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if has_key_param:
                self.send_auth_cookie()
            self.end_headers()
            data_target = find_file("latest_analysis.json", ["data"])
            status_data = {
                "server": "online",
                "platform": "Vercel Cloud 7/24",
                "is_simulating": False,
                "data_available": os.path.exists(data_target),
                "auth_required": True
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        # API: Telegram Yapılandırması
        elif path.endswith("/telegram-config"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if has_key_param:
                self.send_auth_cookie()
            self.end_headers()
            cfg_target = find_file("telegram_config.json", ["data"])
            cfg = {}
            if os.path.exists(cfg_target):
                try:
                    with open(cfg_target, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                except Exception:
                    pass
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

        if path.endswith("/telegram-config"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            cfg_target = find_file("telegram_config.json", ["data"])
            try:
                post_data = json.loads(body)
                cfg = {}
                if os.path.exists(cfg_target):
                    try:
                        with open(cfg_target, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                    except Exception:
                        pass
                if "bot_token" in post_data and post_data["bot_token"]:
                    cfg["bot_token"] = post_data["bot_token"].strip()
                if "chat_id" in post_data:
                    cfg["chat_id"] = str(post_data["chat_id"]).strip()
                if "enabled" in post_data:
                    cfg["enabled"] = bool(post_data["enabled"])
                with open(cfg_target, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Telegram save error: {e}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return

        if path.endswith("/telegram-test"):
            ok = False
            msg = "Telegram modülü yüklenemedi."
            if telegram_notifier:
                ok, msg = telegram_notifier.send_telegram_message("🔔 <b>Antigravity Trade Masası Test Bildirimi</b>")
            self.send_response(200 if ok else 400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok" if ok else "error", "message": msg}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

# Vercel Python Runtime Tarafından Zorunlu Tutulan Üç Değişken (Export)
app = SecureTradeDashboardHandler
application = SecureTradeDashboardHandler
handler = SecureTradeDashboardHandler

def start_server(port=8080):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, SecureTradeDashboardHandler)
    print(f"Sunucu http://localhost:{port} adresinde aktif.")
    httpd.serve_forever()

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    start_server(port)
