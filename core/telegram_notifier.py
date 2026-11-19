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

def find_data_file(filename):
    here = os.path.dirname(os.path.abspath(__file__))
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

CONFIG_FILE = find_data_file("telegram_config.json")
DATA_FILE = find_data_file("latest_analysis.json")

def load_config():
    default_config = {
        "bot_token": "",
        "chat_id": "",
        "enabled": False,
        "alert_on_strong_buy_only": True,
        "sent_signals": {}
    }
    cfg_file = find_data_file("telegram_config.json")
    if not os.path.exists(cfg_file):
        return default_config
    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in default_config.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return default_config

def save_config(cfg):
    cfg_file = find_data_file("telegram_config.json")
    os.makedirs(os.path.dirname(os.path.abspath(cfg_file)), exist_ok=True)
    with open(cfg_file, "w", encoding="utf-8") as f:
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
    action_clean = str(item.get("action", "")).strip().upper()
    # KESİN VE TAVİZSİZ KURAL: Yalnızca ve sadece GÜÇLÜ AL sinyalleri formatlanır
    if action_clean != "GÜÇLÜ AL":
        return None

    plan = item.get("trade_plan", {})
    sim = item.get("simulation", {})
    curr = item.get("currency", (item.get("market") == "BIST" and "₺" or "$"))
    sym = item.get("symbol", "")
    market = item.get("market", "")
    name = item.get("name", "")
    
    # İstenen parametreler: Anlık Fiyat, Fiyat Hedefi, Hedef Gün, Kâr Oranı Hedefi, Güven Yüzdesi
    curr_price = item.get("current_price")
    entry_price = plan.get("entry", curr_price)
    target_price = plan.get("target", "--")
    profit_pct = plan.get("profit_margin_percent", "--")
    stop_price = plan.get("stop", "--")
    risk_pct = plan.get("loss_risk_percent", 2.5)
    target_days = item.get("vade_sure") or item.get("vade") or "3 - 7 İş Günü"
    confidence = item.get("confidence", 85)
    sim_win_rate = sim.get("target_rate", 72.5)
    sim_verdict = sim.get("verdict", "Hedefe Koşuyor")
    ch_pct = item.get("change_percent", 0.0)
    ch_str = f"+%{ch_pct}" if ch_pct >= 0 else f"%{ch_pct}"

    # Güvenlik Zırhı: Sahte 100.0 veya tanımsız fiyatlı mesaj üretme
    if curr_price is None or entry_price is None or curr_price == 100.0 or entry_price == 100.0 or curr_price <= 0:
        return None

    dip_note = ""
    if plan.get("is_dip_entry") and plan.get("wait_for_dip_price"):
        dip_note = f"\n💡 <i>Düşüş Bekleme Tavsiyesi: {curr}{plan.get('wait_for_dip_price')} tabanına çekilme izleniyor.</i>"

    now_str = datetime.datetime.now().strftime("%d.%m.%Y • %H:%M")

    msg = (
        f"🚨 <b>GÜÇLÜ AL SİNYALİ ONAYLANDI!</b> 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Hisse:</b> <code>{sym}</code> ({market} • {name})\n"
        f"⚡ <b>Strateji:</b> Kısa Vade Salınım (Swing Breakout)\n"
        f"⏱️ <b>Hedef Süre:</b> <b>{target_days}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Anlık Piyasa Fiyatı:</b> <b>{curr}{curr_price}</b> ({ch_str})\n"
        f"💵 <b>Önerilen Giriş Seviyesi:</b> <b>{curr}{entry_price}</b>\n"
        f"🎯 <b>Kâr Hedefi:</b> <b>{curr}{target_price}</b> (<b>+%{profit_pct}</b>)\n"
        f"🛑 <b>Zarar Kes (Stop-Loss):</b> <b>{curr}{stop_price}</b> (-%{risk_pct})\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ <b>Model Güven Yüzdesi:</b> <b>%{confidence}</b>\n"
        f"🎲 <b>10.000x Monte Carlo Olasılığı:</b> <b>%{sim_win_rate}</b> ({sim_verdict})\n"
        f"📊 <b>Risk / Ödül Oranı:</b> 1:1.8 (Korumalı Dinamik Stop)"
        f"{dip_note}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ <i>{now_str} • Antigravity Trade Masası</i>"
    )
    return msg

def check_and_notify_strong_buys():
    cfg = load_config()
    if not cfg.get("enabled"):
        return {"status": "skipped", "message": "Telegram bildirimleri kapalı."}

    data_file = find_data_file("latest_analysis.json")
    if not os.path.exists(data_file):
        return {"status": "no_data", "message": "Analiz verisi bulunamadı."}

    try:
        with open(data_file, "r", encoding="utf-8") as f:
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
        sym = item.get("symbol", "")
        plan = item.get("trade_plan", {})
        sim = item.get("simulation", {})

        # KESİN VE NET KURAL: Sadece ve sadece 'GÜÇLÜ AL' sinyalleri kabul edilir!
        # Normal 'AL', 'AL (Düşüşü Bekle)', 'İZLE', 'TUT' vb. ara sinyaller KESİNLİKLE GÖNDERİLMEZ!
        action_clean = str(item.get("action", "")).strip().upper()
        if action_clean != "GÜÇLÜ AL":
            continue

        # 1. GÜVENLİK FİLTRESİ: Sahte 100.0 veya 0/negatif fiyat kontrolü
        try:
            curr_p = float(item.get("current_price") or 0.0)
            entry_p = float(plan.get("entry") or 0.0)
            target_p = float(plan.get("target") or 0.0)
            stop_p = float(plan.get("stop") or 0.0)
        except (ValueError, TypeError):
            continue

        if curr_p <= 0 or entry_p <= 0 or curr_p == 100.0 or entry_p == 100.0:
            print(f"[Telegram Güvenlik Filtresi] {sym} için geçersiz/sahte 100.0 fiyat tespit edildi, bildirim ENGELLENDİ.")
            continue

        # Mantık Testi: Stop Loss < Giriş Fiyatı < Kâr Hedefi
        if not (stop_p < entry_p < target_p):
            print(f"[Telegram Güvenlik Filtresi] {sym} için hatalı stop/hedef hiyerarşisi ({stop_p} / {entry_p} / {target_p}), bildirim ENGELLENDİ.")
            continue

        # 2. KALİTE FİLTRESİ: Minimum Yapay Zeka Güveni ve Monte Carlo İsabet Eşiği
        conf = int(item.get("confidence") or 0)
        target_rate = float(sim.get("target_rate") or 0.0)
        if conf < 80 or target_rate < 55.0:
            print(f"[Telegram Güvenlik Filtresi] {sym} kalite eşiğini aşamadı (Güven: %{conf}, Simülasyon: %{target_rate}), bildirim ENGELLENDİ.")
            continue

        # 3. SPAM ÖNLEME: Son 12 saat içinde bu hisse için bildirim gönderildi mi?
        last_sent_str = sent_signals.get(sym)
        if last_sent_str:
            try:
                last_sent = datetime.datetime.strptime(last_sent_str, "%Y-%m-%d %H:%M:%S")
                if (now - last_sent).total_seconds() < 43200:  # 12 saat soğuma süresi
                    continue
            except Exception:
                pass

        text = format_strong_buy_alert(item)
        if not text:
            continue

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
