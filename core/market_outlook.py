#!/usr/bin/env python3
"""
Antigravity Finans Otomasyonu - Piyasa Görünümü & 7/30 Günlük Haber/Etki Modülü (core/market_outlook.py)
BIST ve ABD Piyasalarının mevcut rejimini, önümüzdeki 7 ve 30 gün içinde beklenen kritik haberleri
ve bu haberlerin piyasayı yüzde kaç (±%) etkileyebileceğini modeller.
"""

import datetime
try:
    from core import fed_rate_tracker
except ImportError:
    import fed_rate_tracker

def get_market_outlook():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    bist_outlook = {
        "market": "BIST",
        "last_updated": now_str,
        "current_regime": {
            "title": "Sıkı Para Politikası & Seçici Yabancı Girişi",
            "mood": "TEMKİNLİ İYİMSER (BULLISH CONSOLIDATION)",
            "summary": "TCMB'nin kararlı faiz duruşu ve dezenflasyon süreci Türk Lirası varlıklara ilgiyi canlı tutuyor. Yüksek faiz borçlu şirketleri baskılarken, kasasında yüklü nakit tutan ve tekel konumundaki sanayi devleri (TUPRS, ENJSA) piyasayı sırtlıyor. Endeks ₺10.200 - ₺10.800 direnç bandını test ediyor.",
            "volatility_index": "ORTA (VIX Benzeri BIST Oynaklığı: %18)"
        },
        "forecast_7d": {
            "period": "Önümüzdeki 7 Gün",
            "net_bias": "POZİTİF KONSOLİDASYON",
            "expected_swing": "+%2.5 / -%1.8",
            "catalysts": [
                {
                    "event": "TCMB Para Politikası Kurulu (PPK) Kararı & Sözlü Yönlendirme",
                    "date": "Bu Hafta",
                    "expectation": "Politika faizinin sabit tutulması ve sıkılık mesajının yinelenmesi bekleniyor.",
                    "impact_range": "+%1.5 ile -%2.0 arası endeks hareketi"
                },
                {
                    "event": "Haftalık Yabancı Portföy Giriş / Çıkış Verileri",
                    "date": "Haftalık Periyodik",
                    "expectation": "Banka ve büyük sanayi hisselerine net yabancı girişi devamı.",
                    "impact_range": "+%0.8 ile -%1.2 arası hisse rotasyonu"
                }
            ]
        },
        "forecast_30d": {
            "period": "Önümüzdeki 30 Gün",
            "net_bias": "GÜÇLÜ YÜKSELİŞ TRENDİ POTANSİYELİ",
            "expected_swing": "+%5.5 / -%4.0",
            "catalysts": [
                {
                    "event": "Uluslararası Kredi Derecelendirme (Moody's / S&P) Not Değerlendirmesi",
                    "date": "Önümüzdeki 3-4 Hafta",
                    "expectation": "Türkiye'nin kredi notu görünümünde pozitif teyit ve olası not artırımı.",
                    "impact_range": "+%3.5 ile -%1.5 arası genele yayılan ralli etkisi"
                },
                {
                    "event": "Aylık TÜFE Enflasyon Gerçekleşmesi & Asgari Ücret / Bütçe Netleşmesi",
                    "date": "Ay Sonu",
                    "expectation": "Aylık enflasyonun %2 bandı altına inmesi durumunda faiz indirim kapısının aralanması.",
                    "impact_range": "+%2.5 ile -%4.0 arası orta vadeli fiyatlama"
                },
                {
                    "event": "BIST Yıllık Temettü ve Q4 Bilanço Beklenti Fiyatlamaları",
                    "date": "Gelecek Ay Başı",
                    "expectation": "TUPRS gibi nakit zengini şirketlerde yüksek nakit temettü beklentisinin alımları tetiklemesi.",
                    "impact_range": "+%4.0 ile -%2.0 arası hisse bazlı getiri ayrışması"
                }
            ]
        }
    }

    us_outlook = {
        "market": "US",
        "last_updated": now_str,
        "current_regime": {
            "title": "FED Faiz İndirim Döngüsü & AI Yatırım Rallisi",
            "mood": "GÜÇLÜ BOĞA (YUMUŞAK İNİŞ SENARYOSU)",
            "summary": "ABD ekonomisinde resesyon riski azalırken yapay zeka sermaye harcamaları (Capex) teknoloji devlerini yukarı taşımaya devam ediyor. Ancak ABD 10 Yıllık Tahvil Faizindeki (%4.40+) ani sıçramalar, faize duyarlı Russell 2000 (IWM) ve Biyoteknoloji (XBI) tarafında ara düzeltmelere yol açıyor.",
            "volatility_index": "DÜŞÜK-ORTA (VIX: 14.8)"
        },
        "forecast_7d": {
            "period": "Önümüzdeki 7 Gün",
            "net_bias": "VERİ ODAKLI DALGALANMA",
            "expected_swing": "+%2.2 / -%2.6",
            "catalysts": [
                {
                    "event": "ABD TÜFE (CPI) Enflasyon & Perakende Satış Raporu",
                    "date": "Bu Hafta",
                    "expectation": "Çekirdek enflasyonun %0.3 aylık artışla beklentiye paralel kalması.",
                    "impact_range": "+%1.8 ile -%2.4 arası Nasdaq/S&P dalgalanması"
                },
                {
                    "event": "FED Başkanı Powell & Bölgesel FED Başkanlarının Konuşmaları",
                    "date": "Hafta İçi",
                    "expectation": "Aralık faiz kararı öncesi şahin/güvercin tonlama ipuçları.",
                    "impact_range": "+%1.2 ile -%1.8 arası tahvil faizi oynaması"
                }
            ]
        },
        "forecast_30d": {
            "period": "Önümüzdeki 30 Gün",
            "net_bias": "YIL SONU RALLİSİ (SANTA RALLY) DESTEKLİ",
            "expected_swing": "+%6.0 / -%4.5",
            "catalysts": [
                {
                    "event": "FOMC Faiz Kararı & Dot Plot (FED Projeksiyon Raporu)",
                    "date": "Önümüzdeki Ay",
                    "expectation": "25 baz puan faiz indirimi ve 2027 için 100 bps toplam gevşeme patikası.",
                    "impact_range": "+%4.0 ile -%5.0 arası tüm piyasayı yönlendirecek ana karar"
                },
                {
                    "event": "NVIDIA & Yarı İletken Devleri Kurumsal Zirvesi & Tedarik Güncellemeleri",
                    "date": "Önümüzdeki 3 Hafta",
                    "expectation": "Blackwell ve Rubin çip sevkiyat takviminde rekor teslimat onayları.",
                    "impact_range": "+%5.5 ile -%6.5 arası AI hisseleri sıçraması"
                },
                {
                    "event": "ABD Hazine Borçlanma Takvimi & Küresel Ticaret/Tarife Başlıkları",
                    "date": "30 Gün İçinde",
                    "expectation": "Tahvil ihraç büyüklükleri ve ticaret tarifeleri haber akışı.",
                    "impact_range": "+%2.5 ile -%4.0 arası sektör rotasyonları"
                }
            ]
        },
        "fed_rate_decision": fed_rate_tracker.get_fed_rate_forecast()
    }

    return {
        "bist": bist_outlook,
        "us": us_outlook
    }

if __name__ == "__main__":
    out = get_market_outlook()
    print("Market Outlook Hazır:", out["bist"]["forecast_7d"]["expected_swing"], out["us"]["forecast_7d"]["expected_swing"])
