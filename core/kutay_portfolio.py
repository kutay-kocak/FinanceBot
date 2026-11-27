#!/usr/bin/env python3
"""
Kutay'ın Portföy ve Pozisyon Takip Modülü (core/kutay_portfolio.py v4)
- Stop seviyeleri kaldırılmıştır (Kullanıcı kararı).
- Her aktif pozisyon için 6 aylık gerçek piyasa teknik seviyeleriyle (EMA20, EMA50, EMA200, ATR, 20g/60g/6ay zirveleri)
  örtüşen, abartısız 3 vade hedefi sunulur:
    1) Kısa Vade (3 - 10 Gün)
    2) Orta Vade (2 Hafta - 2 Ay)
    3) Uzun Vade (2 Ay - 6 Ay)
- En çok önerilen vade süresi net biçimde vurgulanır.
- Kapatılan pozisyonlar (XBI: $157.50 -> $158.00) sade ve net biçimde Eski Pozisyonlar başlığında tutulur.
"""

import datetime

TSI = datetime.timezone(datetime.timedelta(hours=3))

def now_tsi_str():
    return datetime.datetime.now(TSI).strftime("%Y-%m-%d %H:%M:%S")

KUTAY_POSITIONS_DEF = [
    {
        "symbol": "THYAO",
        "raw_symbol": "THYAO.IS",
        "name": "Türk Hava Yolları",
        "market": "BIST",
        "currency": "₺",
        "entry_cost": 327.00,
        "confidence": 84,
        "estimated_accuracy": 81,
        "accuracy_summary": "EMA20 Desteği Üzerinde Tutunma & Güçlü Kargo Geliri",
        "accuracy_details": "Hisse ₺308.50 (EMA20) ve ₺303.90 (EMA200) desteklerinin üzerinde tutunuyor; 20/60 günlük ₺333.50 ve 6 aylık ₺355.50 dirençleri gerçekçi hedef basamaklarıdır.",
        "recommended_key": "long",
        "recommended_vade": "Uzun Vade (2 Ay - 6 Ay)",
        "recommended_reason": "₺327.00 maliyetinizin üzerinde anlamlı net kâr (+%8.56) elde etmek için kış sezonu sonrasında 6 aylık zirve olan ₺355.00 bandının beklenmesi en yüksek isabetli stratejidir.",
        "targets": {
            "short": {
                "label": "Kısa Vade (3 - 10 Gün)",
                "price": 324.00,
                "note": "Ara tepki direnci (maliyete yaklaşma)"
            },
            "medium": {
                "label": "Orta Vade (2 Hafta - 2 Ay)",
                "price": 336.00,
                "note": "Son 20 ve 60 günlük tepe (₺333.50) kırılım bandı"
            },
            "long": {
                "label": "Uzun Vade (2 Ay - 6 Ay)",
                "price": 355.00,
                "note": "Son 6 aylık zirve (₺355.50) ana direnç hedefi"
            }
        }
    },
    {
        "symbol": "TUPRS",
        "raw_symbol": "TUPRS.IS",
        "name": "Tüpraş Türkiye Petrol Rafinerileri",
        "market": "BIST",
        "currency": "₺",
        "entry_cost": 334.50,
        "confidence": 88,
        "estimated_accuracy": 85,
        "accuracy_summary": "EMA200 (₺329.50) Ana Tabanı & Yüksek Net Nakit Gücü",
        "accuracy_details": "₺334.50 maliyetiniz EMA200 (₺329.51) ana kurumsal tabanının hemen üzerinde çok sağlıklı konumda; EMA50 (₺350.46) ve 20 günlük tepe (₺364.50) yakın hedeflerdir.",
        "recommended_key": "medium",
        "recommended_vade": "Orta Vade (2 Hafta - 2 Ay)",
        "recommended_reason": "Maliyetiniz çok güçlü bir tabanda olduğu için 2 hafta - 2 ay içinde son 20 günlük direnç olan ₺364.00 bölgesinde (+%8.82 net kâr) dengeli ve yüksek olasılıklı getiri sunmaktadır.",
        "targets": {
            "short": {
                "label": "Kısa Vade (3 - 10 Gün)",
                "price": 349.00,
                "note": "EMA50 (₺350.46) hareketli ortalama direnci"
            },
            "medium": {
                "label": "Orta Vade (2 Hafta - 2 Ay)",
                "price": 364.00,
                "note": "Son 20 günlük zirve (₺364.50) test bölgesi"
            },
            "long": {
                "label": "Uzun Vade (2 Ay - 6 Ay)",
                "price": 388.00,
                "note": "Temettü dönemi ve net nakit faiz geliri hedef bandı"
            }
        }
    },
    {
        "symbol": "AVGO",
        "raw_symbol": "AVGO",
        "name": "Broadcom Inc.",
        "market": "US",
        "currency": "$",
        "entry_cost": 353.87,
        "confidence": 85,
        "estimated_accuracy": 80,
        "accuracy_summary": "Aşırı Satım Tepkisi (RSI ~40) & Özel AI Çip (ASIC) Bilançosu",
        "accuracy_details": "Sert düzeltme sonrası RSI 40 destek bölgesinde dengeleniyor; yukarıda EMA20 ($327.20), EMA50 ($339.60) ve EMA200 ($369.53) teknik basamakları yer alıyor.",
        "recommended_key": "long",
        "recommended_vade": "Uzun Vade (2 Ay - 6 Ay)",
        "recommended_reason": "$353.87 maliyetiniz mevcut düzeltme fiyatının üzerinde kaldığı için kısa vadeli tepkiler başabaşa yetmez; Aralık bilançosu ve 2027 AI çip siparişleriyle EMA200 ($372.00, +%5.12 kâr) hedefini beklemek en rasyonel yaklaşımdır.",
        "targets": {
            "short": {
                "label": "Kısa Vade (3 - 10 Gün)",
                "price": 322.00,
                "note": "EMA20 ($327.20) öncesi ilk teknik tepki bandı"
            },
            "medium": {
                "label": "Orta Vade (2 Hafta - 2 Ay)",
                "price": 348.00,
                "note": "Bilanço dönemi EMA50 ($339.60) üstü toparlanma"
            },
            "long": {
                "label": "Uzun Vade (2 Ay - 6 Ay)",
                "price": 372.00,
                "note": "EMA200 ($369.53) ve son 20g zirve ($369.82) bölgesi"
            }
        }
    },
    {
        "symbol": "IWM",
        "raw_symbol": "IWM",
        "name": "iShares Russell 2000 ETF",
        "market": "US",
        "currency": "$",
        "entry_cost": 288.00,
        "confidence": 75,
        "estimated_accuracy": 74,
        "accuracy_summary": "Tahvil Faizi Hassasiyeti & EMA200 ($287.82) Mıknatıs Etkisi",
        "accuracy_details": "Günlük oynaklığı düşük (%2.18 ATR) bir endeks ETF'sidir; sırasıyla EMA50 ($277.54), EMA200 ($287.82) ve 60 günlük tepe ($296.18) seviyeleri gerçekçi hedeflerdir.",
        "recommended_key": "long",
        "recommended_vade": "Uzun Vade (2 Ay - 6 Ay)",
        "recommended_reason": "ABD 10Y tahvil faizi (%4.85) baskısı nedeniyle orta vadede $287.50 başabaş bölgesine ulaşması, 2-6 aylık vadede ise $298.00 (+%3.47 net kâr) hedefine geçmesi gerçekçi senaryodur.",
        "targets": {
            "short": {
                "label": "Kısa Vade (3 - 10 Gün)",
                "price": 275.50,
                "note": "EMA20 ($272.12) üstü & EMA50 ($277.54) testi"
            },
            "medium": {
                "label": "Orta Vade (2 Hafta - 2 Ay)",
                "price": 287.50,
                "note": "EMA200 ($287.82) ve başabaş denge bölgesi"
            },
            "long": {
                "label": "Uzun Vade (2 Ay - 6 Ay)",
                "price": 298.00,
                "note": "60 günlük zirve ($296.18) üstü gerçekçi kanal"
            }
        }
    }
]

KUTAY_CLOSED_POSITIONS_DEF = [
    {
        "symbol": "XBI",
        "raw_symbol": "XBI",
        "name": "SPDR S&P Biotech ETF",
        "market": "US",
        "currency": "$",
        "entry_cost": 157.50,
        "exit_price": 158.00,
        "pnl_amount": 0.50,
        "pnl_percent": 0.32,
        "is_profitable": True,
        "status_tag": "KAPATILDI (+%0.32)"
    }
]

def generate_dynamic_status(sym, curr_p, entry_c, diff, diff_pct, currency):
    is_profitable = diff >= 0
    pnl_amount = round(diff, 2)
    pnl_pct = round(diff_pct, 2)

    if pnl_pct >= 5.0:
        status_tag = f"GÜÇLÜ KÂRDA (+%{pnl_pct}) 🚀"
        status_type = "strong_profit"
    elif pnl_pct > 0.25:
        status_tag = f"KÂRDA (+%{pnl_pct}) 📈"
        status_type = "profit"
    elif -0.35 <= pnl_pct <= 0.25:
        status_tag = "BAŞABAŞ DENGEDE ⚖️"
        status_type = "neutral"
    elif -5.0 <= pnl_pct < -0.35:
        status_tag = f"MALİYET ALTINDA (-%{abs(pnl_pct)})"
        status_type = "pullback"
    else:
        status_tag = f"GERİ ÇEKİLMEDE (-%{abs(pnl_pct)})"
        status_type = "loss"

    theses = {
        "THYAO": "EMA20 (₺308.50) üzerinde dengeleniyor; kargo ve dış hat yolcu hacmi orta-uzun vadeli toparlanmayı destekliyor.",
        "TUPRS": "EMA200 (₺329.50) kurumsal desteği üzerinde güçlü duruyor; yüksek net nakit pozisyonu faiz ortamında ekstra getiri sağlıyor.",
        "AVGO": "Teknoloji satışlarıyla geri çekilse de Google ve Meta özel AI çip (ASIC) talebi ve VMware nakit akışı uzun vadeli ana katalizördür.",
        "IWM": "ABD tahvil faizlerindeki hareketlere duyarlı seyrediyor; tahvil getirilerindeki sakinleşmeyle birlikte EMA200 ($287.80) bandına yönelmesi beklenir."
    }
    base_thesis = theses.get(sym, "Teknik ve makro göstergeler izleniyor.")

    if is_profitable:
        status_sentence = f"Anlık fiyat ({currency}{curr_p:.2f}), alış maliyetinizin ({currency}{entry_c:.2f}) üzerinde +%{pnl_pct} (+{currency}{pnl_amount:.2f} / hisse) kârda."
    else:
        status_sentence = f"Anlık fiyat ({currency}{curr_p:.2f}), alış maliyetinizin ({currency}{entry_c:.2f}) -%{abs(pnl_pct)} (-{currency}{abs(pnl_amount):.2f} / hisse) altında."

    special_analysis = f"{status_sentence} {base_thesis}"
    return status_tag, status_type, special_analysis

def evaluate_kutay_positions(all_market_assets):
    price_map = {}
    for a in all_market_assets:
        price_map[a["symbol"]] = a["current_price"]
        if "raw_symbol" in a:
            price_map[a["raw_symbol"]] = a["current_price"]

    evaluated = []
    total_winners = 0
    total_losers = 0

    for pos in KUTAY_POSITIONS_DEF:
        sym = pos["symbol"]
        curr_p = price_map.get(sym) or price_map.get(pos.get("raw_symbol")) or pos["entry_cost"]
        entry_c = pos["entry_cost"]
        diff = curr_p - entry_c
        diff_pct = round((diff / entry_c) * 100, 2)

        is_profitable = diff >= 0
        if is_profitable:
            total_winners += 1
        else:
            total_losers += 1

        status_tag, status_type, special_analysis = generate_dynamic_status(
            sym=sym,
            curr_p=curr_p,
            entry_c=entry_c,
            diff=diff,
            diff_pct=diff_pct,
            currency=pos["currency"]
        )

        # 3 vade hedefi için hem maliyete göre hem cari fiyata göre kâr/potansiyel oranlarını hesapla
        computed_targets = {}
        for t_key in ("short", "medium", "long"):
            t_info = dict(pos["targets"][t_key])
            t_price = t_info["price"]
            t_info["gain_from_cost_pct"] = round(((t_price - entry_c) / entry_c) * 100, 2)
            t_info["gain_from_current_pct"] = round(((t_price - curr_p) / curr_p) * 100, 2)
            t_info["is_recommended"] = (t_key == pos["recommended_key"])
            computed_targets[t_key] = t_info

        pos_dict = {
            "symbol": sym,
            "raw_symbol": pos.get("raw_symbol", sym),
            "name": pos["name"],
            "market": pos["market"],
            "currency": pos["currency"],
            "entry_cost": entry_c,
            "current_price": round(curr_p, 2),
            "pnl_amount": round(diff, 2),
            "pnl_percent": diff_pct,
            "is_profitable": is_profitable,
            "confidence": pos["confidence"],
            "estimated_accuracy": pos["estimated_accuracy"],
            "accuracy_summary": pos["accuracy_summary"],
            "accuracy_details": pos["accuracy_details"],
            "status_tag": status_tag,
            "status_type": status_type,
            "special_analysis": special_analysis,
            "recommended_key": pos["recommended_key"],
            "recommended_vade": pos["recommended_vade"],
            "recommended_reason": pos["recommended_reason"],
            "vade": pos["recommended_vade"],
            "targets": computed_targets
        }
        evaluated.append(pos_dict)

    closed_evaluated = [dict(c) for c in KUTAY_CLOSED_POSITIONS_DEF]

    sorted_positions = sorted(evaluated, key=lambda x: x["pnl_percent"], reverse=True)
    leader = sorted_positions[0] if sorted_positions else None

    if leader and leader["pnl_percent"] > 0:
        leader_title = f"{leader['symbol']} Kâr Lideri"
        leader_val = f"+%{leader['pnl_percent']} 🚀"
        leader_color = "emerald"
    elif leader:
        leader_title = f"{leader['symbol']} En Dayanıklı"
        leader_val = f"%{leader['pnl_percent']} ⚖️"
        leader_color = "amber"
    else:
        leader_title = "Lider Yok"
        leader_val = "--"
        leader_color = "slate"

    return {
        "metadata": {
            "owner": "Kutay",
            "last_evaluated": now_tsi_str(),
            "total_positions": len(evaluated),
            "closed_count": len(closed_evaluated),
            "profitable_count": total_winners,
            "pullback_count": total_losers,
            "portfolio_health": f"{total_winners} Kârda • {total_losers} Maliyet Altı",
            "leader_title": leader_title,
            "leader_val": leader_val,
            "leader_color": leader_color
        },
        "positions": evaluated,
        "closed_positions": closed_evaluated
    }
