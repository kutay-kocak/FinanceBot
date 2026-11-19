#!/usr/bin/env python3
"""
Hafif ve Hızlı Fiyat Güncelleme Motoru (core/price_updater.py)
Ağır 10.000 Monte Carlo simülasyonunu tekrar çalıştırmadan,
sadece anlık hisse fiyatlarını ve kâr oranlarını saniyeler içinde günceller.
"""

import os
import sys
import json
import datetime
import urllib.request
import urllib.parse
import types

here = os.path.dirname(os.path.abspath(__file__))
if "core" not in sys.modules:
    core_pkg = types.ModuleType("core")
    core_dir = os.path.join(here, "core") if not here.endswith("core") else here
    core_pkg.__path__ = [core_dir]
    sys.modules["core"] = core_pkg

sys.path.insert(0, here)
sys.path.insert(0, os.path.dirname(here))

try:
    import kutay_portfolio
except ImportError:
    from core import kutay_portfolio

def find_data_file(filename):
    candidates = [
        os.path.join(here, filename),
        os.path.join(here, "data", filename),
        os.path.join(os.path.dirname(here), "data", filename),
        os.path.join(os.path.dirname(here), filename)
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[1] if os.path.exists(os.path.join(here, "data")) else candidates[0]

DATA_FILE = find_data_file("latest_analysis.json")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_fast_quote(symbol):
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range=1d&interval=5m"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            meta = data["chart"]["result"][0]["meta"]
            curr_price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose")
            if curr_price and prev_close:
                ch_p = round(((curr_price - prev_close) / prev_close) * 100, 2)
            else:
                ch_p = 0.0
            return round(curr_price, 2), ch_p
    except Exception:
        return None, None

def update_prices_only():
    if not os.path.exists(DATA_FILE):
        return None

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Hızlı Fiyat Güncellemesi Başladı...")

    price_cache = {}

    def update_item_price(item):
        raw_sym = item.get("raw_symbol", item.get("symbol"))
        if raw_sym not in price_cache:
            p, ch = fetch_fast_quote(raw_sym)
            if p is not None:
                price_cache[raw_sym] = (p, ch)
            else:
                price_cache[raw_sym] = (item.get("current_price"), item.get("change_percent"))

        new_p, new_ch = price_cache[raw_sym]
        if new_p:
            item["current_price"] = new_p
            item["change_percent"] = new_ch
            
            # Kâr marjını güncel fiyata göre yeniden hesapla
            target = item["trade_plan"]["target"]
            item["trade_plan"]["profit_margin_percent"] = round(((target - new_p) / new_p) * 100, 2)

    # US Market listesi
    for it in data.get("us_market", []):
        update_item_price(it)

    # BIST Market listesi
    for it in data.get("bist_market", []):
        update_item_price(it)

    # Hiyerarşi listeleri
    hier = data.get("hierarchy", {})
    for k in ("kisa_vade", "orta_vade", "uzun_vade"):
        for it in hier.get(k, []):
            update_item_price(it)

    # Kutay'ın Pozisyonlarını güncel fiyatlarla yeniden hesapla
    all_assets = data.get("us_market", []) + data.get("bist_market", [])
    data["kutay_portfolio"] = kutay_portfolio.evaluate_kutay_positions(all_assets)

    # Öğrenme ve kendini geliştirme raporunu senkronize et
    try:
        from core import learning_tracker
        data["learning_report"] = learning_tracker.load_ledger()
    except Exception as e:
        print(f"Learning report senkronizasyon hatası: {e}")

    # BIST ve US Piyasa Görünümü & 7/30 Günlük Beklentileri senkronize et
    try:
        from core import market_outlook
        from core import fed_rate_tracker
        outlook = market_outlook.get_market_outlook()
        data["market_outlook"] = outlook
        data["fed_rate_decision"] = fed_rate_tracker.get_fed_rate_forecast()
    except Exception as e:
        print(f"Market outlook senkronizasyon hatası: {e}")

    # Metadata güncelleme: Fiyat güncelleme tarihi ile Simülasyon tarihini ayır
    if "metadata" not in data:
        data["metadata"] = {}

    if "last_simulation_run" not in data["metadata"]:
        data["metadata"]["last_simulation_run"] = data["metadata"].get("last_run", now_str)

    data["metadata"]["last_price_update"] = now_str

    save_targets = {DATA_FILE}
    root_target = os.path.join(os.path.dirname(here), "latest_analysis.json") if here.endswith("core") else os.path.join(here, "latest_analysis.json")
    save_targets.add(root_target)
    for target_path in save_targets:
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Uyarı: {target_path} dosyasına yazılamadı: {e}")

    # Kısa vadeli GÜÇLÜ AL sinyallerini kontrol et ve Telegram bildirimi gönder
    try:
        try:
            import telegram_notifier
        except ImportError:
            from core import telegram_notifier
        telegram_notifier.check_and_notify_strong_buys()
    except Exception as e:
        print(f"Telegram bildirim kontrolü hatası: {e}")

    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [OK] Fiyatlar ve kâr oranları güncellendi!")
    return data

if __name__ == "__main__":
    update_prices_only()
