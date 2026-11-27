#!/usr/bin/env python3
"""
Hafif ve Hızlı Fiyat & Haber Güncelleme Motoru (core/price_updater.py v3)
- ThreadPoolExecutor ile tüm BIST & ABD hisselerini paralel olarak ~1 saniyede çeker.
- Her sunucuda (Windows, GitHub Actions, Vercel) sabit Türkiye Saati (TSİ / UTC+3) kullanır.
- Yazılabilir ortamlarda tüm JSON kopyalarını + HTML gömülü veriyi günceller;
  Vercel salt-okunur bulut ortamında /tmp önbelleğine yazar ve güncel veriyi doğrudan döndürür.
"""

import os
import sys
import json
import datetime
import tempfile
import urllib.request
import urllib.parse
import types
from concurrent.futures import ThreadPoolExecutor

TSI = datetime.timezone(datetime.timedelta(hours=3))

def now_tsi():
    return datetime.datetime.now(TSI)

here = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(here) if here.endswith("core") else here

if "core" not in sys.modules:
    core_pkg = types.ModuleType("core")
    core_dir = os.path.join(root_dir, "core")
    core_pkg.__path__ = [core_dir] if os.path.exists(core_dir) else [root_dir]
    sys.modules["core"] = core_pkg

for p in (os.path.join(root_dir, "core"), root_dir):
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from core import kutay_portfolio

TMP_DATA_FILE = os.path.join(tempfile.gettempdir(), "latest_analysis.json")

def get_best_data_file():
    candidates = [
        os.path.join(root_dir, "data", "latest_analysis.json"),
        os.path.join(root_dir, "latest_analysis.json"),
        TMP_DATA_FILE
    ]
    existing = [c for c in candidates if os.path.exists(c)]
    if not existing:
        return candidates[0]
    existing.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return existing[0]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def fetch_fast_quote(symbol):
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range=1d&interval=5m"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            meta = data["chart"]["result"][0]["meta"]
            curr_price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose")
            if curr_price and curr_price > 0 and curr_price != 100.0:
                if prev_close and prev_close > 0:
                    ch_p = round(((curr_price - prev_close) / prev_close) * 100, 2)
                else:
                    ch_p = 0.0
                return round(curr_price, 2), ch_p
    except Exception:
        pass
    return None, None

def update_prices_only(refresh_news=True):
    source_file = get_best_data_file()
    if not os.path.exists(source_file):
        return None

    with open(source_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    now_dt = now_tsi()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_dt.strftime('%H:%M:%S')} TSİ] Hızlı Fiyat Güncellemesi Başladı...")

    # Tüm benzersiz sembolleri topla ve paralel çek
    unique_symbols = set()
    for grp in (data.get("us_market", []), data.get("bist_market", [])):
        for it in grp:
            raw_sym = it.get("raw_symbol", it.get("symbol"))
            if raw_sym:
                unique_symbols.add(raw_sym)
    hier = data.get("hierarchy", {})
    for k in ("kisa_vade", "orta_vade", "uzun_vade"):
        for it in hier.get(k, []):
            raw_sym = it.get("raw_symbol", it.get("symbol"))
            if raw_sym:
                unique_symbols.add(raw_sym)
    # Kutay aktif pozisyon sembollerini de garanti altına al
    for pos in kutay_portfolio.KUTAY_POSITIONS_DEF:
        unique_symbols.add(pos.get("raw_symbol", pos["symbol"]))

    price_cache = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        fut_map = {sym: ex.submit(fetch_fast_quote, sym) for sym in unique_symbols}
        for sym, fut in fut_map.items():
            try:
                p, ch = fut.result()
                if p is not None:
                    price_cache[sym] = (p, ch)
            except Exception:
                pass

    def update_item_price(item):
        raw_sym = item.get("raw_symbol", item.get("symbol"))
        if raw_sym in price_cache:
            new_p, new_ch = price_cache[raw_sym]
            item["current_price"] = new_p
            item["change_percent"] = new_ch
            target = item["trade_plan"]["target"]
            item["trade_plan"]["profit_margin_percent"] = round(((target - new_p) / new_p) * 100, 2)
            item["updated_at"] = now_str

    for it in data.get("us_market", []):
        update_item_price(it)
    for it in data.get("bist_market", []):
        update_item_price(it)
    for k in ("kisa_vade", "orta_vade", "uzun_vade"):
        for it in hier.get(k, []):
            update_item_price(it)

    # BIST Enflasyon Kuralı: Orta ve Uzun vadede %5 veya altı kâr hedefli BIST tahminleri siteden gizlenir
    def _bist_margin_ok(item):
        if item.get("market") == "BIST" and item.get("vade_group") in ("Orta Vade", "Uzun Vade"):
            if item.get("trade_plan", {}).get("profit_margin_percent", 0) <= 5.0:
                return False
        return True

    data["bist_market"] = [it for it in data.get("bist_market", []) if _bist_margin_ok(it)]
    for k in ("orta_vade", "uzun_vade"):
        if k in hier:
            hier[k] = [it for it in hier.get(k, []) if _bist_margin_ok(it)]

    # Kutay'ın Pozisyonlarını güncel fiyatlarla yeniden hesapla (price_cache yedekli)
    all_assets = list(data.get("us_market", [])) + list(data.get("bist_market", []))
    existing_syms = {a.get("raw_symbol", a.get("symbol")) for a in all_assets}
    for sym, (p_val, _) in price_cache.items():
        if sym not in existing_syms:
            all_assets.append({"symbol": sym.replace(".IS", ""), "raw_symbol": sym, "current_price": p_val})

    data["kutay_portfolio"] = kutay_portfolio.evaluate_kutay_positions(all_assets)

    # Öğrenme raporunu senkronize et
    try:
        from core import learning_tracker
        if refresh_news:
            data["learning_report"] = learning_tracker.verify_and_learn_from_history(all_assets)
        else:
            data["learning_report"] = learning_tracker.load_ledger()
    except Exception as e:
        print(f"Learning report senkronizasyon hatası: {e}")

    # Piyasa Görünümü, Canlı Haberler ve FED Radarını yenile
    if refresh_news or "market_outlook" not in data or "fed_rate_decision" not in data:
        try:
            from core import market_outlook
            from core import fed_rate_tracker
            outlook = market_outlook.get_market_outlook()
            data["market_outlook"] = outlook
            data["fed_rate_decision"] = outlook.get("us", {}).get("fed_rate_decision") or fed_rate_tracker.get_fed_rate_forecast()
        except Exception as e:
            print(f"Market outlook senkronizasyon hatası: {e}")

    if "metadata" not in data:
        data["metadata"] = {}

    if "last_simulation_run" not in data["metadata"]:
        data["metadata"]["last_simulation_run"] = data["metadata"].get("last_run", now_str)

    data["metadata"]["last_price_update"] = now_str
    data["metadata"]["timezone"] = "TSİ (UTC+3)"

    save_targets = [
        os.path.join(root_dir, "data", "latest_analysis.json"),
    ]
    wrote_project_disk = False
    for target_path in save_targets:
        try:
            parent_d = os.path.dirname(target_path)
            if os.path.exists(parent_d):
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                wrote_project_disk = True
        except Exception:
            pass

    # Vercel / bulut salt-okunur dosya sistemi için /tmp önbelleği
    try:
        with open(TMP_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # 0ms Gömülü Veri Zırhı: Yazılabilir ortamda HTML dosyalarına göm
    if wrote_project_disk:
        try:
            from core import embed_data
            embed_data.embed()
        except Exception as e:
            print(f"Gömülü veri zırhı notu: {e}")

    # Kısa vadeli GÜÇLÜ AL sinyallerini kontrol et ve Telegram bildirimi gönder
    try:
        from core import telegram_notifier
        telegram_notifier.check_and_notify_strong_buys()
    except Exception as e:
        print(f"Telegram bildirim kontrolü hatası: {e}")

    print(f"[{now_tsi().strftime('%H:%M:%S')} TSİ] [OK] Fiyatlar, portföy kârları ve haber verileri güncellendi!")
    return data

if __name__ == "__main__":
    update_prices_only(refresh_news=True)
