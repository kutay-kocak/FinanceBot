#!/usr/bin/env python3
"""
Antigravity Finans Otomasyonu - Telegram Sinyal Botu (core/telegram_notifier.py)
Kısa vadede 'GÜÇLÜ AL' sinyali tespit edildiğinde kullanıcıya anlık Telegram bildirimi gönderir.
"""

import os
import sys
import json
import datetime
import urllib.request
import urllib.parse
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "telegram_config.json")
DATA_FILE = os.path.join(DATA_DIR, "latest_analysis.json")

def load_config():
    default_config = {
        "bot_token": "",
        "chat_id": "",
        "enabled": False,
        "alert_on_strong_buy_only": True,
        "sent_signals": {}
    }
    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Default alanları garanti et
            for k, v in default_config.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return default_config

def save_config(cfg):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def send_telegram_message(text, bot_token=None, chat_id=None, parse_mode="HTML"):
    cfg = load_config()
    token = bot_token or cfg.get("bot_token")
    cid = chat_id or cfg.get("chat_id")

    if not token or not cid:
        return False, "Bot Token veya Chat ID tanımlanmamış."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=data_bytes, 
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if res_data.get("ok"):
                return True, "Mesaj başarıyla iletildi."
            return False, f"Telegram hatası: {res_data}"
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        return False, f"HTTP Hatası {e.code}: {err_msg}"
    except Exception as e:
        return False, f"Bağlantı hatası: {str(e)}"

def format_strong_buy_alert(item):
    plan = item.get("trade_plan", {})
    sim = item.get("simulation", {})
    curr = item.get("currency", "$")
    sym = item.get("symbol", "")
    market = item.get("market", "")
    name = item.get("name", "")
    entry = plan.get("entry", item.get("current_price"))
    target = plan.get("target")
    profit_pct = plan.get("profit_margin_percent")
    stop = plan.get("stop")
    conf = item.get("confidence", 80)
    sim_rate = sim.get("target_rate", 70)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    msg = (
        f"🚨 <b>GÜÇLÜ AL SİNYALİ TESPİT EDİLDİ!</b> 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Varlık:</b> <code>{sym}</code> ({market} • {name})\n"
        f"⚡ <b>Strateji:</b> Kısa Vade (3 - 7 Günlük Kırılım)\n"
        f"💵 <b>Giriş Fiyatı:</b> <b>{curr}{entry}</b>\n"
        f"🎯 <b>Kâr Hedefi:</b> <b>{curr}{target}</b> (+%{profit_pct})\n"
        f"🛑 <b>Zarar Kes (Stop):</b> <b>{curr}{stop}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ <b>AI Güven Oranı:</b> %{conf}\n"
        f"🎲 <b>10.000x Monte Carlo Başarı İhtimali:</b> %{sim_rate}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ <i>Tarih: {now_str} • Antigravity Trade Masası</i>"
    )
    return msg

def check_and_notify_strong_buys():
    cfg = load_config()
    if not cfg.get("enabled"):
        return {"status": "skipped", "message": "Telegram bildirimleri kapalı."}

    if not os.path.exists(DATA_FILE):
        return {"status": "no_data", "message": "Analiz verisi bulunamadı."}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Kısa vadeli fırsatlar öncelikli
    hier = data.get("hierarchy", {})
    kisa_list = hier.get("kisa_vade", [])
    all_assets = data.get("us_market", []) + data.get("bist_market", [])
    
    candidates = kisa_list if kisa_list else all_assets
    sent_signals = cfg.get("sent_signals", {})
    now = datetime.datetime.now()
    alerts_sent = []

    for item in candidates:
        action = item.get("action", "")
        sym = item.get("symbol", "")

        # Yalnızca GÜÇLÜ AL sinyalleri
        if "GÜÇLÜ" in action and "AL" in action:
            # Son 12 saat içinde bu hisse için bildirim gönderildi mi?
            last_sent_str = sent_signals.get(sym)
            if last_sent_str:
                try:
                    last_sent = datetime.datetime.strptime(last_sent_str, "%Y-%m-%d %H:%M:%S")
                    if (now - last_sent).total_seconds() < 43200:  # 12 saat
                        continue
                except Exception:
                    pass

            text = format_strong_buy_alert(item)
            ok, resp_msg = send_telegram_message(text)
            if ok:
                sent_signals[sym] = now.strftime("%Y-%m-%d %H:%M:%S")
                alerts_sent.append(sym)
                print(f"[Telegram Bildirimi İletildi]: {sym} GÜÇLÜ AL!")

    cfg["sent_signals"] = sent_signals
    save_config(cfg)
    return {"status": "ok", "alerts_sent": alerts_sent}

if __name__ == "__main__":
    cfg = load_config()
    print("Mevcut Telegram Yapılandırması:", {
        "enabled": cfg.get("enabled"),
        "has_token": bool(cfg.get("bot_token")),
        "has_chat_id": bool(cfg.get("chat_id"))
    })
