#!/usr/bin/env python3
"""
Antigravity Finans Otomasyonu - Vercel WSGI & Yerel Sunucu Motoru (app.py v3)
- Tüm buton rotalarını (/api/refresh-prices, /api/refresh-news, /api/simulate, /api/telegram-config, /api/telegram-test) tam destekler.
- Vercel salt-okunur bulut ortamında /tmp önbelleğini kullanır ve güncel veriyi doğrudan JSON yanıtında döndürür.
- Sayfa açılışında veri 15 dakikadan eskiyse otomatik olarak canlı fiyatları ve TSİ saatini tazeler.
"""

import datetime
import json
import os
import sys
import tempfile
import types
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TSI = datetime.timezone(datetime.timedelta(hours=3))
TMP_ANALYSIS_FILE = os.path.join(tempfile.gettempdir(), "latest_analysis.json")
TMP_TG_FILE = os.path.join(tempfile.gettempdir(), "telegram_config.json")

core_dir = os.path.join(BASE_DIR, "core")
if "core" not in sys.modules:
    core_pkg = types.ModuleType("core")
    core_pkg.__path__ = [core_dir] if os.path.exists(core_dir) else [BASE_DIR]
    sys.modules["core"] = core_pkg

for p in ([core_dir, BASE_DIR] if os.path.exists(core_dir) else [BASE_DIR]):
    if p not in sys.path:
        sys.path.insert(0, p)

def find_file(filename, subfolders=None):
    candidates = []
    if subfolders:
        for sf in subfolders:
            candidates.append(os.path.join(BASE_DIR, sf, filename))
    candidates.append(os.path.join(BASE_DIR, filename))
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

def get_freshest_analysis_path():
    candidates = [
        os.path.join(BASE_DIR, "data", "latest_analysis.json"),
        TMP_ANALYSIS_FILE,
    ]
    existing = [c for c in candidates if os.path.exists(c)]
    if not existing:
        return candidates[0]
    existing.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return existing[0]

def is_data_stale(data_dict, max_age_seconds=900):
    try:
        ts_str = data_dict.get("metadata", {}).get("last_price_update", "")
        if not ts_str:
            return True
        clean_ts = ts_str.replace(" TSİ", "").strip()
        dt = datetime.datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TSI)
        age = (datetime.datetime.now(TSI) - dt).total_seconds()
        return age > max_age_seconds
    except Exception:
        return False

def json_response(start_response, cors_headers, payload, status="200 OK"):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = cors_headers + [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body)))
    ]
    start_response(status, headers)
    return [body]

def read_post_json(environ):
    try:
        content_length = int(environ.get("CONTENT_LENGTH") or 0)
        if content_length > 0:
            raw = environ["wsgi.input"].read(content_length).decode("utf-8")
            return json.loads(raw)
    except Exception:
        pass
    return {}

def app(environ, start_response):
    """Vercel Python WSGI Giriş Noktası"""
    raw_path = environ.get("PATH_INFO", "/")
    query_str = environ.get("QUERY_STRING", "")
    q_params = urllib.parse.parse_qs(query_str)
    action_param = q_params.get("action", [""])[0]

    # Vercel dahili rewrite durumunda gerçek URL yolunu yakala
    if raw_path in ("/app.py", "app.py") and action_param:
        path = f"/api/{action_param}"
    elif raw_path in ("/app.py", "app.py"):
        req_uri = environ.get("REQUEST_URI") or environ.get("RAW_URI") or "/"
        path = urllib.parse.urlparse(req_uri).path or "/"
    elif action_param:
        path = f"/api/{action_param}"
    else:
        path = raw_path

    method = environ.get("REQUEST_METHOD", "GET").upper()

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
        html_file = find_file("index.html", ["web", "public"])
        if os.path.exists(html_file):
            with open(html_file, "rb") as f:
                body = f.read()
            headers = cors_headers + [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body)))
            ]
            start_response("200 OK", headers)
            return [body]
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"index.html bulunamadi."]

    # 2. Analiz Verisi (/api/analysis veya /latest_analysis.json)
    if path.endswith("/analysis") or path.endswith("latest_analysis.json"):
        data_file = get_freshest_analysis_path()
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    data_obj = json.load(f)
                # Veri 15 dakikadan eskiyse otomatik canlı fiyat ve haber güncellemesi yap
                if is_data_stale(data_obj, 900):
                    try:
                        from core import price_updater
                        fresh = price_updater.update_prices_only(refresh_news=True)
                        if fresh:
                            data_obj = fresh
                    except Exception as e:
                        print(f"Otomatik tazeleme notu: {e}")
                return json_response(start_response, cors_headers, data_obj)
            except Exception as e:
                return json_response(start_response, cors_headers, {"error": str(e)}, "500 Internal Server Error")
        return json_response(start_response, cors_headers, {"error": "Henüz analiz verisi oluşturulmadı."})

    # 3. Sunucu Durumu (/api/status)
    if path.endswith("/status"):
        data_file = get_freshest_analysis_path()
        status_data = {
            "server": "online",
            "platform": "Antigravity Cloud & Local Hybrid",
            "is_simulating": False,
            "data_available": os.path.exists(data_file),
            "auth_required": False
        }
        return json_response(start_response, cors_headers, status_data)

    # 4. Hızlı Fiyat Güncelleme (/api/refresh-prices)
    if path.endswith("/refresh-prices") and method == "POST":
        try:
            from core import price_updater
            updated = price_updater.update_prices_only(refresh_news=False)
            return json_response(start_response, cors_headers, {
                "status": "ok",
                "message": "Hisse fiyatları ve portföy kâr/zarar oranları güncellendi.",
                "analysis": updated
            })
        except Exception as e:
            return json_response(start_response, cors_headers, {"status": "error", "error": str(e)}, "500 Internal Server Error")

    # 5. Piyasa & Haberleri Yenile (/api/refresh-news veya /api/refresh-macro)
    if (path.endswith("/refresh-news") or path.endswith("/refresh-macro")) and method == "POST":
        try:
            from core import price_updater
            updated = price_updater.update_prices_only(refresh_news=True)
            return json_response(start_response, cors_headers, {
                "status": "ok",
                "message": "Canlı piyasa haberleri, BIST/US makro göstergeler ve beklentiler yenilendi.",
                "analysis": updated
            })
        except Exception as e:
            return json_response(start_response, cors_headers, {"status": "error", "error": str(e)}, "500 Internal Server Error")

    # 6. 10.000x Monte Carlo Simülasyonu (/api/simulate)
    if path.endswith("/simulate") and method == "POST":
        try:
            from core import engine
            updated = engine.run_full_pipeline()
            return json_response(start_response, cors_headers, {
                "status": "completed",
                "message": "10.000 seanslık Zaman Makinesi simülasyonu tamamlandı.",
                "analysis": updated
            })
        except Exception as e:
            return json_response(start_response, cors_headers, {"status": "error", "message": str(e)}, "500 Internal Server Error")

    # 7. Telegram Yapılandırması (/api/telegram-config)
    if path.endswith("/telegram-config"):
        cfg_file = TMP_TG_FILE if os.path.exists(TMP_TG_FILE) else find_file("telegram_config.json", ["data"])
        if method == "POST":
            post_data = read_post_json(environ)
            cfg = {}
            if os.path.exists(cfg_file):
                try:
                    with open(cfg_file, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                except Exception:
                    pass
            if "bot_token" in post_data and post_data["bot_token"]:
                cfg["bot_token"] = post_data["bot_token"].strip()
            if "chat_id" in post_data:
                cfg["chat_id"] = str(post_data["chat_id"]).strip()
            if "enabled" in post_data:
                cfg["enabled"] = bool(post_data["enabled"])
            cfg["alert_on_strong_buy_only"] = True

            saved = False
            try:
                t_cfg = os.path.join(BASE_DIR, "data", "telegram_config.json")
                with open(t_cfg, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                saved = True
            except Exception:
                pass
            if not saved:
                try:
                    with open(TMP_TG_FILE, "w", encoding="utf-8") as f:
                        json.dump(cfg, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return json_response(start_response, cors_headers, {"status": "ok", "message": "Telegram ayarları kaydedildi."})
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
                "alert_on_strong_buy_only": True
            }
            return json_response(start_response, cors_headers, safe_cfg)

    # 8. Telegram Test Bildirimi (/api/telegram-test)
    if path.endswith("/telegram-test") and method == "POST":
        post_data = read_post_json(environ)
        token = post_data.get("bot_token") or None
        cid = post_data.get("chat_id") or None
        ok = False
        msg = "Telegram modülü bulunamadı."
        try:
            from core import telegram_notifier
            test_msg = (
                "🤖 <b>Antigravity Trade Masası Telegram Botu Aktif!</b>\n\n"
                "✅ Bağlantı başarıyla doğrulandı.\n"
                "🎯 Sadece <b>GÜÇLÜ AL</b> etiketli ve kalite barajını geçen sinyaller iletilecektir."
            )
            ok, msg = telegram_notifier.send_telegram_message(test_msg, bot_token=token, chat_id=cid)
        except Exception as e:
            msg = str(e)
        status_code = "200 OK" if ok else "400 Bad Request"
        return json_response(start_response, cors_headers, {"status": "ok" if ok else "error", "message": msg}, status_code)

    # 9. Statik Dosyalar
    clean_path = path.lstrip("/")
    static_file = find_file(clean_path, ["web", "public"])
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

    start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"Not Found"]

application = app
handler = app

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
