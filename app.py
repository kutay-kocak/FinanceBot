#!/usr/bin/env python3
"""
Antigravity Finans Otomasyonu - Vercel WSGI & Yerel Sunucu Motoru (app.py)
Vercel Python Runtime için tam uyumlu standart WSGI (Web Server Gateway Interface) uygulaması.
"""

import json
import os
import sys
import types
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Klasörsüz (düz dizin) veya alt klasörlü (core/, data/, web/) yapıları destekle
if "core" not in sys.modules:
    core_pkg = types.ModuleType("core")
    core_dir = os.path.join(BASE_DIR, "core")
    core_pkg.__path__ = [core_dir] if os.path.exists(core_dir) else [BASE_DIR]
    sys.modules["core"] = core_pkg

sys.path.insert(0, BASE_DIR)
if os.path.exists(os.path.join(BASE_DIR, "core")):
    sys.path.insert(0, os.path.join(BASE_DIR, "core"))

def find_file(filename, subfolders=None):
    candidates = [os.path.join(BASE_DIR, filename)]
    if subfolders:
        for sf in subfolders:
            candidates.append(os.path.join(BASE_DIR, sf, filename))
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

def app(environ, start_response):
    """Vercel Python WSGI Giriş Noktası"""
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET").upper()

    # CORS & Güvenlik Başlıkları
    cors_headers = [
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
        ("Cache-Control", "no-cache, no-store, must-revalidate")
    ]

    if method == "OPTIONS":
        start_response("200 OK", cors_headers)
        return [b""]

    # 1. Ana Sayfa (index.html)
    if path in ("/", "/index.html", ""):
        html_file = find_file("index.html", ["public", "web"])
        if os.path.exists(html_file):
            with open(html_file, "rb") as f:
                body = f.read()
            headers = cors_headers + [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body)))
            ]
            start_response("200 OK", headers)
            return [body]
        else:
            start_response("404 Not Found", [("Content-Type", "text/plain")])
            return [b"index.html bulunamadi."]

    # 2. Analiz Verisi (/api/analysis veya /latest_analysis.json)
    if path.endswith("/analysis") or path.endswith("latest_analysis.json"):
        data_file = find_file("latest_analysis.json", ["data"])
        if os.path.exists(data_file):
            with open(data_file, "rb") as f:
                body = f.read()
            headers = cors_headers + [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body)))
            ]
            start_response("200 OK", headers)
            return [body]
        else:
            err_body = json.dumps({"error": "Henüz analiz verisi oluşturulmadı."}).encode("utf-8")
            start_response("200 OK", cors_headers + [("Content-Type", "application/json; charset=utf-8")])
            return [err_body]

    # 3. Sunucu Durumu (/api/status)
    if path.endswith("/status"):
        data_file = find_file("latest_analysis.json", ["data"])
        status_data = {
            "server": "online",
            "platform": "Vercel Cloud 7/24 Kesintisiz",
            "is_simulating": False,
            "data_available": os.path.exists(data_file),
            "auth_required": False
        }
        body = json.dumps(status_data).encode("utf-8")
        headers = cors_headers + [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body)))
        ]
        start_response("200 OK", headers)
        return [body]

    # 4. Telegram Yapılandırması (/api/telegram-config)
    if path.endswith("/telegram-config"):
        cfg_file = find_file("telegram_config.json", ["data"])
        if method == "POST":
            try:
                content_length = int(environ.get("CONTENT_LENGTH", 0))
                req_body = environ["wsgi.input"].read(content_length).decode("utf-8")
                post_data = json.loads(req_body)
                cfg = {}
                if os.path.exists(cfg_file):
                    with open(cfg_file, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                if "bot_token" in post_data and post_data["bot_token"]:
                    cfg["bot_token"] = post_data["bot_token"].strip()
                if "chat_id" in post_data:
                    cfg["chat_id"] = str(post_data["chat_id"]).strip()
                if "enabled" in post_data:
                    cfg["enabled"] = bool(post_data["enabled"])
                with open(cfg_file, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Telegram save error: {e}")
            start_response("200 OK", cors_headers + [("Content-Type", "application/json")])
            return [json.dumps({"status": "ok"}).encode("utf-8")]
        else:
            cfg = {}
            if os.path.exists(cfg_file):
                try:
                    with open(cfg_file, "r", encoding="utf-8") as f:
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
            body = json.dumps(safe_cfg).encode("utf-8")
            start_response("200 OK", cors_headers + [("Content-Type", "application/json; charset=utf-8")])
            return [body]

    # 5. Fiyat Güncelleme Tetikleyicisi (/api/refresh-prices)
    if path.endswith("/refresh-prices") and method == "POST":
        try:
            try:
                import price_updater
            except ImportError:
                from core import price_updater
            price_updater.update_prices_only()
            msg = "Fiyatlar güncellendi."
        except Exception as e:
            msg = f"Güncelleme notu: {e}"
        body = json.dumps({"status": "ok", "message": msg}).encode("utf-8")
        start_response("200 OK", cors_headers + [("Content-Type", "application/json; charset=utf-8")])
        return [body]

    # 6. Telegram Test Bildirimi (/api/telegram-test)
    if path.endswith("/telegram-test") and method == "POST":
        ok = False
        msg = "Telegram modülü bulunamadı."
        try:
            try:
                import telegram_notifier
            except ImportError:
                from core import telegram_notifier
            ok, msg = telegram_notifier.send_telegram_message("🔔 <b>Antigravity Trade Masası Test Bildirimi</b>")
        except Exception as e:
            msg = str(e)
        status_code = "200 OK" if ok else "400 Bad Request"
        body = json.dumps({"status": "ok" if ok else "error", "message": msg}).encode("utf-8")
        start_response(status_code, cors_headers + [("Content-Type", "application/json; charset=utf-8")])
        return [body]

    # 7. Statik Dosyalar (js, css, png vb.)
    clean_path = path.lstrip("/")
    static_file = find_file(clean_path, ["public", "web"])
    if os.path.isfile(static_file):
        with open(static_file, "rb") as f:
            body = f.read()
        mime = "text/plain"
        if static_file.endswith(".html"): mime = "text/html; charset=utf-8"
        elif static_file.endswith(".js"): mime = "application/javascript; charset=utf-8"
        elif static_file.endswith(".css"): mime = "text/css; charset=utf-8"
        elif static_file.endswith(".json"): mime = "application/json; charset=utf-8"
        headers = cors_headers + [
            ("Content-Type", mime),
            ("Content-Length", str(len(body)))
        ]
        start_response("200 OK", headers)
        return [body]

    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"Not Found"]

# Vercel WSGI Entrypoint İhracı
application = app
handler = app

# Yerel test ve bağımsız çalıştırma (python app.py)
if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    print(f"WSGI Sunucu http://localhost:{port} adresinde aktif.")
    httpd = make_server("0.0.0.0", port, app)
    httpd.serve_forever()
