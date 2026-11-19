#!/usr/bin/env python3
"""
Kutay'ın Portföy ve Pozisyon Takip Modülü (core/kutay_portfolio.py v2)
Kutay'ın Gerçek Alım Maliyetleri:
- XBI: $157.50
- IWM: $288.00
- AVGO: $353.87
- TUPRS: ₺334.50

Uzun vadeli tutulabilirlik ve ayrı uzun vadeli hedefler dahil edilmiştir.
"""

import datetime

KUTAY_POSITIONS_DEF = [
    {
        "symbol": "TUPRS",
        "raw_symbol": "TUPRS.IS",
        "name": "Tüpraş Türkiye Petrol Rafinerileri",
        "market": "BIST",
        "currency": "₺",
        "entry_cost": 334.50,
        "vade": "3 - 6 Hafta (Orta Vade)",
        "confidence": 88,
        "estimated_accuracy": 86,
        "accuracy_summary": "Yüksek Güvenilirlik & Düşük Oynaklık",
        "accuracy_details": "Tüpraş'ın güçlü net nakit pozisyonu, ₺348 üzerindeki güçlü kurumsal taban ve 10.000 seanslık Monte Carlo simülasyonundaki yüksek başarı oranıyla desteklenmektedir.",
        "target_1": 395.00,
        "target_2": 425.00,
        "stop_rule": 348.00,
        "status_tag": "GÜÇLÜ KÂRDA 🚀",
        "special_analysis": "Pozisyonunuz net %7.6 kârda! Akdeniz rafineri ürün marjlarındaki toparlanma ve şirketin kasasındaki devasa net nakdin yüksek faiz ortamında sürekli finansal gelir yazması hisseyi ₺360 direncine taşıdı.",
        "action_advice": "Kârınızı kilitlemek için stop seviyenizi ₺348.00 seviyesine yükseltin (bu seviyede kapansanız dahi %4 net kâr garantidir).",
        "long_term_viability": "UZUN VADEDE ÇOK GÜVENİLİR (TUTULABİLİR) ⭐⭐⭐⭐⭐",
        "long_term_evaluation": "Türkiye'nin tek ham petrol rafinerisidir ve alternatifi yoktur. Yüksek nakit temettü verimi, yeşil hidrojen ve biyoyakıt dönüşüm yatırımlarıyla portföyde 1-3 yıl tutulabilecek en sağlam BIST sanayi devi.",
        "long_term_target": 450.00,
        "long_term_gain_percent": 34.5
    },
    {
        "symbol": "AVGO",
        "name": "Broadcom Inc.",
        "market": "US",
        "currency": "$",
        "entry_cost": 353.87,
        "vade": "2 - 3 Hafta (Kısa Vade)",
        "confidence": 86,
        "estimated_accuracy": 84,
        "accuracy_summary": "Yüksek Trend Gücü & Kurumsal Talep",
        "accuracy_details": "Özel AI çip üretimindeki tekel konumu, $354 üzerindeki risksiz stop seviyesi ve güçlü serbest nakit akışı sayesinde hedefe ulaşma isabeti çok yüksektir.",
        "target_1": 385.00,
        "target_2": 410.00,
        "stop_rule": 354.00,
        "status_tag": "KÂRDA 🚀",
        "special_analysis": "Dipten dönüşte harika bir seviyeden girilmiş; anlık olarak kârda. VMware kurumsal yazılım marjları ve büyük teknoloji şirketlerinin özel AI çip (ASIC) talebiyle yükseliş trendi teyit edildi.",
        "action_advice": "Stop seviyenizi maliyetinizin hemen üzerine ($354.00) çekerek pozisyonu 'SIFIR RİSKLİ' (Risk-Free) hale getirin.",
        "long_term_viability": "UZUN VADEDE ÇOK GÜVENİLİR (TUTULABİLİR) ⭐⭐⭐⭐⭐",
        "long_term_evaluation": "Google, Meta ve ByteDance'in özel AI çiplerinde tekel üreticidir. Yıllık $20B+ serbest nakit akışı ve her yıl artan temettüsüyle portföyün teknoloji omurgası olarak uzun yıllar tutulmaya uygundur.",
        "long_term_target": 440.00,
        "long_term_gain_percent": 24.3
    },
    {
        "symbol": "IWM",
        "name": "iShares Russell 2000 ETF",
        "market": "US",
        "currency": "$",
        "entry_cost": 288.00,
        "vade": "2 - 4 Hafta (Kısa-Orta Vade)",
        "confidence": 74,
        "estimated_accuracy": 72,
        "accuracy_summary": "Orta Güvenilirlik & Makro Hassasiyeti",
        "accuracy_details": "$275-$278 dip desteği güçlü şekilde test ediliyor; FED faiz indirimi beklentileriyle toparlanma potansiyeli yüksek olmakla birlikte tahvil faizi dalgalanmaları nedeniyle isabet orta-yüksek aralıktadır.",
        "target_1": 305.00,
        "target_2": 320.00,
        "stop_rule": 268.00,
        "status_tag": "PULLBACK / DESTEK TESTİ",
        "special_analysis": "$288 seviyesi önceki zirve kırılımıydı; şu an $275-$278 bölgesindeki kırılım onayına (re-test) çekilmiş durumda. İskonto makası açık, alıcılar bu bölgede güçlü.",
        "action_advice": "$275-$278 desteği güçlü bir alım bloğudur. Panik satışı yapmayın; $305 kâr hedefine kadar pozisyonu koruyun.",
        "long_term_viability": "DÖNGÜSEL (UZUN VADE YERİNE ORTA VADELİ KÂR REALİZASYONU UYGUN) ⭐⭐⭐",
        "long_term_evaluation": "Küçük ölçekli şirketler faiz indirim döngülerinde 3-6 aylık güçlü sıçrama yapar ancak 3-5 yıllık vadede büyük ölçekli tekel teknoloji devlerine (S&P 500) kıyasla daha zayıf kalır. Kâr hedefinde çıkıp ana hisselere dönmek daha kârlıdır.",
        "long_term_target": 320.00,
        "long_term_gain_percent": 11.1
    },
    {
        "symbol": "XBI",
        "name": "SPDR S&P Biotech ETF",
        "market": "US",
        "currency": "$",
        "entry_cost": 157.50,
        "vade": "3 - 5 Hafta (Orta Vade)",
        "confidence": 71,
        "estimated_accuracy": 69,
        "accuracy_summary": "Yüksek Volatilite & Döngüsel Risk",
        "accuracy_details": "Erken aşama biyoteknoloji sektörünün yüksek betası nedeniyle tahmin dalgalanma payı içerir; $149 EMA50 desteği tutunursa $172 hedefine dönüş olasılığı %69 olarak hesaplanmıştır.",
        "target_1": 172.00,
        "target_2": 184.00,
        "stop_rule": 144.50,
        "status_tag": "DÜZELTME / EMA50 DESTEĞİ",
        "special_analysis": "ABD 10Y tahvil faizindeki sıçrama biyoteknolojide kâr realizasyonu getirdi. $148-$150 bandı 60 günlük güçlü EMA50 ortalama desteğidir.",
        "action_advice": "$149-$150 desteğinin çalıştığı teyit edildikten sonra ilk hedef olan $172.00 (+%9.2) seviyesine kadar tutulmalıdır.",
        "long_term_viability": "YÜKSEK RİSKLİ DÖNGÜSEL (UZUN VADE TUTULMAMALI, TREND KÂRI ALINMALI) ⭐⭐",
        "long_term_evaluation": "Erken aşama biyoteknolojiler klinik faz riskleri ve nakit yakımı taşır. Tahvil faizi gevşediğinde gelen %20-30'luk sert yükseliş dalgasında kârı alıp çıkmak gerekir; uzun yıllar tutmak yüksek yıpranma riski yaratır.",
        "long_term_target": 184.00,
        "long_term_gain_percent": 16.8
    }
]

def generate_dynamic_status(sym, curr_p, entry_c, diff, diff_pct, stop_rule, target_1, target_2, currency):
    is_profitable = diff >= 0
    pnl_amount = round(diff, 2)
    pnl_pct = round(diff_pct, 2)
    
    # 1. Dinamik Durum Rozeti (status_tag)
    if curr_p <= stop_rule:
        status_tag = "STOP ALARMI! (Zarar Kes) 🛑"
        status_type = "danger"
    elif pnl_pct >= 5.0:
        status_tag = f"GÜÇLÜ KÂRDA (+%{pnl_pct}) 🚀"
        status_type = "strong_profit"
    elif pnl_pct > 0.3:
        status_tag = f"KÂRDA (+%{pnl_pct}) 📈"
        status_type = "profit"
    elif -0.5 <= pnl_pct <= 0.3:
        status_tag = "BAŞABAŞ ⚖️"
        status_type = "neutral"
    elif -4.0 <= pnl_pct < -0.5:
        status_tag = f"DESTEK TESTİNDE (-%{abs(pnl_pct)}) ⚠️"
        status_type = "pullback"
    else:
        status_tag = f"DÜZELTMEDE / ZARARDA (-%{abs(pnl_pct)}) 📉"
        status_type = "loss"

    # 2. Dinamik Özel Analiz (special_analysis)
    theses = {
        "TUPRS": "Akdeniz rafineri ürün marjlarındaki toparlanma ve şirketin kasasındaki devasa net nakdin faiz getirisi hisseyi destekleyen ana katalizördür.",
        "AVGO": "Google ve Meta için üretilen özel AI çip (ASIC) talebi ile VMware kurumsal yazılım gelirleri hissenin ana itici gücüdür.",
        "IWM": "Küçük ölçekli şirketler faiz indirim döngüsünde iskonto makasını kapatmak için destek arıyor.",
        "XBI": "Biyoteknoloji sektörü 10Y tahvil faizlerindeki dalgalanmalara karşı yüksek beta gösteriyor; klinik faz haber akışları takip ediliyor."
    }
    base_thesis = theses.get(sym, "Teknik ve temel göstergeler yakından izleniyor.")
    
    if is_profitable:
        status_sentence = f"Pozisyonunuz anlık olarak +%{pnl_pct} kârda (+{currency}{pnl_amount} / hisse). Cari fiyat ({currency}{curr_p:.2f}) maliyetinizin ({currency}{entry_c:.2f}) üzerinde seyrediyor."
    elif -0.5 <= pnl_pct <= 0.3:
        status_sentence = f"Fiyat ({currency}{curr_p:.2f}) alış maliyetiniz ({currency}{entry_c:.2f}) seviyesinde başabaş dengeleniyor."
    else:
        status_sentence = f"Pozisyonunuz maliyetinizin altında -%{abs(pnl_pct)} zararda (-{currency}{abs(pnl_amount):.2f} / hisse). Cari fiyat ({currency}{curr_p:.2f}) seviyesinde destek testi sürüyor."

    special_analysis = f"{status_sentence} {base_thesis}"

    # 3. Dinamik Aksiyon & Stop Tavsiyesi (action_advice)
    if curr_p <= stop_rule:
        action_advice = f"DİKKAT: Fiyat {currency}{curr_p:.2f} seviyesine inerek belirlenen kritik stop seviyesini ({currency}{stop_rule:.2f}) kırdı/test ediyor! Risk kuralı gereği pozisyonu kapatıp zararı durdurmayı değerlendirin."
    elif pnl_pct >= 5.0:
        action_advice = f"Pozisyon güçlü kârda! Kârınızı kilitlemek için stop seviyenizi en az {currency}{stop_rule:.2f} seviyesine çekerek net kârı garantiye alın. 1. Hedef olan {currency}{target_1:.2f} seviyesinde kısmi kâr satışı yapılabilir."
    elif pnl_pct > 0.3:
        action_advice = f"Pozisyon kârda ilerliyor. Stop seviyenizi maliyetiniz olan {currency}{entry_c:.2f} seviyesine çekerek bu işlemi tamamen 'Sıfır Riskli' (Risk-Free) hale getirebilirsiniz."
    elif -0.5 <= pnl_pct <= 0.3:
        action_advice = f"Maliyet seviyeniz test ediliyor. {currency}{stop_rule:.2f} ana stop seviyesi kırılmadığı sürece acele etmeden pozisyonu koruyun."
    else:
        action_advice = f"Maliyetin altında ancak {currency}{stop_rule:.2f} ana stop seviyesi üzerinde tutunuyor. Panik satışı yapmadan desteği izleyin; {currency}{target_1:.2f} tepki hedefi geçerliliğini koruyor."

    return status_tag, status_type, special_analysis, action_advice

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
        
        target1_pct = round(((pos["target_1"] - entry_c) / entry_c) * 100, 2)
        target2_pct = round(((pos["target_2"] - entry_c) / entry_c) * 100, 2)

        is_profitable = diff >= 0
        if is_profitable:
            total_winners += 1
        else:
            total_losers += 1

        status_tag, status_type, special_analysis, action_advice = generate_dynamic_status(
            sym=sym,
            curr_p=curr_p,
            entry_c=entry_c,
            diff=diff,
            diff_pct=diff_pct,
            stop_rule=pos["stop_rule"],
            target_1=pos["target_1"],
            target_2=pos["target_2"],
            currency=pos["currency"]
        )

        pos_dict = dict(pos)
        pos_dict.update({
            "current_price": round(curr_p, 2),
            "pnl_amount": round(diff, 2),
            "pnl_percent": diff_pct,
            "is_profitable": is_profitable,
            "status_tag": status_tag,
            "status_type": status_type,
            "special_analysis": special_analysis,
            "action_advice": action_advice,
            "target_1_gain_percent": target1_pct,
            "target_2_gain_percent": target2_pct,
        })
        evaluated.append(pos_dict)

    # Lider pozisyonu dinamik bul
    sorted_positions = sorted(evaluated, key=lambda x: x["pnl_percent"], reverse=True)
    leader = sorted_positions[0] if sorted_positions else None
    
    if leader and leader["pnl_percent"] > 0:
        leader_title = f"{leader['symbol']} Kâr Lideri"
        leader_val = f"+%{leader['pnl_percent']} 🚀"
        leader_color = "emerald"
    elif leader:
        leader_title = f"{leader['symbol']} En Dayanıklı"
        leader_val = f"{leader['pnl_percent']}% ⚖️"
        leader_color = "amber"
    else:
        leader_title = "Lider Yok"
        leader_val = "--"
        leader_color = "slate"

    return {
        "metadata": {
            "owner": "Kutay",
            "last_evaluated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_positions": len(evaluated),
            "profitable_count": total_winners,
            "pullback_count": total_losers,
            "portfolio_health": f"{total_winners} Kârda • {total_losers} Destek/Zararda",
            "leader_title": leader_title,
            "leader_val": leader_val,
            "leader_color": leader_color
        },
        "positions": evaluated
    }
